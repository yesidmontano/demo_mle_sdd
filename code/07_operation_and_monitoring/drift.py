"""Drift y señales de producto de `conversion-sesion`. Una sola lógica, sin E/S de modelos.

La usan el dashboard y los gates `alert-backtest` y `false-positive-budget`: si cada uno calculara
lo suyo, el dashboard podría mostrar verde donde el backtest dice alerta.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("code/03-data_preparation").resolve()))
import preprocessing as pp

REFERENCE_PATH = Path("data/silver/monitoring_reference.json")
NUMERIC = ["num_passengers", "purchase_lead", "length_of_stay", "flight_hour", "flight_duration"]
CATEGORICAL = ["sales_channel", "trip_type", "flight_day", "route", "booking_origin", *pp.WANTS]
FEATURES = [*NUMERIC, *CATEGORICAL]
HIGH_CARD = ["route", "booking_origin"]
IN = "in_"

WINDOW = 200
BINS = 10
MIN_SHARE = 0.01
WARN_PSI, ALERT_PSI = 0.10, 0.25
OTHER = "otros"
EPS = 1e-4

# señal -> (aviso, alerta, acción). Espejo de la tabla de `conversion-sesion-monitoring`.
ACTIONS = {
    "psi_features": "investigar el origen del desvío; si persiste, abrir un change de reentrenamiento",
    "psi_score": "investigar el origen del desvío; si persiste, abrir un change de reentrenamiento",
    "latency_p99": "revisar carga y tamaño del modelo",
    "rejection_rate": "revisar el contrato de entrada con el productor de datos",
    "unseen_categories": "reentrenar con las nuevas categorías",
    "intervention_rate": "revisar umbral y distribución de puntuaciones",
}


# --- referencia ---------------------------------------------------------------------------------

def _cat_key(s: pd.Series, kept) -> pd.Series:
    s = s.astype(str)
    return s.where(s.isin(kept), OTHER)


def _freq(counts) -> list:
    c = np.asarray(counts, float)
    return (c / c.sum()).tolist()


def build_reference(train: pd.DataFrame, scores_ref, k_fraction: float) -> dict:
    """Cortes y frecuencias de train por feature, y de las puntuaciones de referencia."""
    ref = {"window": WINDOW, "k_fraction": k_fraction, "numeric": {}, "categorical": {}, "known": {}}
    for c in NUMERIC:
        edges = sorted(set(np.quantile(train[c], np.linspace(0, 1, BINS + 1)[1:-1]).tolist()))
        idx = np.searchsorted(edges, train[c].to_numpy(), side="right")
        ref["numeric"][c] = {"edges": edges, "freq": _freq(np.bincount(idx, minlength=len(edges) + 1))}
    for c in CATEGORICAL:
        share = train[c].astype(str).value_counts(normalize=True)
        kept = share[share >= MIN_SHARE].index.tolist()
        keys = kept + [OTHER]
        counts = _cat_key(train[c], kept).value_counts().reindex(keys).fillna(0)
        ref["categorical"][c] = {"keys": keys, "freq": _freq(counts.to_numpy())}
    for c in HIGH_CARD:
        ref["known"][c] = sorted(train[c].astype(str).unique().tolist())
    edges = sorted(set(np.quantile(scores_ref, np.linspace(0, 1, BINS + 1)[1:-1]).tolist()))
    idx = np.searchsorted(edges, np.asarray(scores_ref), side="right")
    ref["score"] = {"edges": edges, "freq": _freq(np.bincount(idx, minlength=len(edges) + 1))}
    return ref


def save_reference(ref: dict, path: Path = REFERENCE_PATH) -> None:
    path.write_text(json.dumps(ref, indent=1))


def load_reference(path: Path = REFERENCE_PATH) -> dict:
    return json.loads(path.read_text())


# --- PSI ----------------------------------------------------------------------------------------

def psi(expected, actual) -> float:
    e, a = np.clip(np.asarray(expected, float), EPS, None), np.clip(np.asarray(actual, float), EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def severity(value: float, warn: float, alert: float) -> str:
    return "alerta" if value >= alert else "aviso" if value >= warn else "ok"


def feature_psi(ref: dict, window: pd.DataFrame) -> dict:
    """PSI de cada feature de entrada de una ventana con columnas sin prefijo."""
    out = {}
    for c in NUMERIC:
        edges = ref["numeric"][c]["edges"]
        idx = np.searchsorted(edges, window[c].to_numpy(), side="right")
        out[c] = psi(ref["numeric"][c]["freq"], _freq(np.bincount(idx, minlength=len(edges) + 1)))
    for c in CATEGORICAL:
        keys = ref["categorical"][c]["keys"]
        counts = _cat_key(window[c], keys[:-1]).value_counts().reindex(keys).fillna(0)
        out[c] = psi(ref["categorical"][c]["freq"], _freq(counts.to_numpy()))
    return out


def score_psi(ref: dict, scores) -> float:
    edges = ref["score"]["edges"]
    idx = np.searchsorted(edges, np.asarray(scores), side="right")
    return psi(ref["score"]["freq"], _freq(np.bincount(idx, minlength=len(edges) + 1)))


def window_alert(ref: dict, window: pd.DataFrame, alert_psi: float = ALERT_PSI) -> tuple[bool, float, str]:
    """(¿alerta?, PSI máximo, feature) de una ventana de entradas."""
    p = feature_psi(ref, window)
    worst = max(p, key=p.get)
    return p[worst] >= alert_psi, p[worst], worst


# --- ventanas para el backtest ------------------------------------------------------------------

def sample_windows(df: pd.DataFrame, n_windows: int, size: int, seed: int, drift: dict | None = None):
    """Ventanas aleatorias de `df`; con `drift`, sobremuestrea `column == value` por `oversample_factor`."""
    rng = np.random.default_rng(seed)
    w = None
    if drift:
        w = np.where(df[drift["column"]].astype(str) == drift["value"], float(drift["oversample_factor"]), 1.0)
        w = w / w.sum()
    for _ in range(n_windows):
        yield df.iloc[rng.choice(len(df), size=size, replace=False, p=w)]


def backtest(ref: dict, df: pd.DataFrame, n_windows: int, size: int, seed: int,
             drift: dict | None = None, alert_psi: float = ALERT_PSI) -> dict:
    res = [window_alert(ref, w, alert_psi) for w in sample_windows(df, n_windows, size, seed, drift)]
    maxes = [r[1] for r in res]
    return {"alert_rate": float(np.mean([r[0] for r in res])), "max_psi": maxes,
            "median_max_psi": float(np.median(maxes))}


# --- inferencias -> señales ---------------------------------------------------------------------

def strip_inputs(inf: pd.DataFrame) -> pd.DataFrame:
    """Entradas de las inferencias con los nombres originales de las columnas."""
    cols = {f"{IN}{c}": c for c in pp.INPUT_COLUMNS if f"{IN}{c}" in inf.columns}
    return inf.rename(columns=cols)


def _signal(name, value, warn, alert, unit="", enough=True, detail=None, two_sided=False):
    if not enough:
        status = "datos insuficientes"
    else:
        v = abs(value) if two_sided else value
        status = severity(v, warn, alert)
    return {"name": name, "value": None if value is None else round(float(value), 4), "warn": warn,
            "alert": alert, "unit": unit, "status": status, "action": ACTIONS[name], "detail": detail or {}}


def signals(inf: pd.DataFrame, ref: dict, size: int = WINDOW) -> list[dict]:
    """Estado de cada señal de la spec sobre la última ventana de `size` inferencias."""
    inf = inf.sort_values("timestamp_utc")
    last = inf.tail(size)
    ok = strip_inputs(inf[inf["status"] == "ok"]).tail(size)
    enough_ok, enough_all = len(ok) >= size, len(last) >= size
    out = []
    if enough_ok:
        p = feature_psi(ref, ok)
        worst = max(p, key=p.get)
        out.append(_signal("psi_features", p[worst], WARN_PSI, ALERT_PSI, "PSI", detail={"feature": worst, "por_feature": p}))
        sp = score_psi(ref, ok["prob_conversion"])
    else:
        out.append(_signal("psi_features", None, WARN_PSI, ALERT_PSI, "PSI", enough=False))
        sp = None
    out.append(_signal("psi_score", sp, WARN_PSI, ALERT_PSI, "PSI", enough=enough_ok))
    lat = last["latency_ms"]
    out.append(_signal("latency_p99", np.percentile(lat, 99) if len(lat) else None, 250, 500, "ms", enough=enough_all))
    out.append(_signal("rejection_rate", (last["status"] != "ok").mean() if len(last) else None, 0.01, 0.05, "", enough=enough_all))
    unseen = None
    if enough_ok:
        u = pd.concat([~ok[c].astype(str).isin(ref["known"][c]) for c in HIGH_CARD], axis=1).any(axis=1)
        unseen = float(u.mean())
    out.append(_signal("unseen_categories", unseen, 0.05, 0.15, "", enough=enough_ok))
    k = ref["k_fraction"]
    rate = float(ok["intervene"].mean()) if enough_ok else None
    out.append(_signal("intervention_rate", None if rate is None else rate - k, 0.05, 0.10, "pp",
                       enough=enough_ok, detail={"tasa": rate, "esperada": k}, two_sided=True))
    return out


def rolling_psi(inf: pd.DataFrame, ref: dict, size: int = WINDOW, step: int = 25) -> list[dict]:
    """Señales en ventanas móviles de `size` inferencias ok, en orden temporal (un punto por ventana)."""
    ok = strip_inputs(inf[inf["status"] == "ok"].sort_values("timestamp_utc")).reset_index(drop=True)
    out = []
    for end in range(size, len(ok) + 1, step):
        w = ok.iloc[end - size:end]
        p = feature_psi(ref, w)
        worst = max(p, key=p.get)
        unseen = pd.concat([~w[c].astype(str).isin(ref["known"][c]) for c in HIGH_CARD], axis=1).any(axis=1).mean()
        out.append({"end": w["timestamp_utc"].iloc[-1].isoformat(), "n": end, "psi_max": p[worst], "feature": worst,
                    "psi_score": score_psi(ref, w["prob_conversion"]), "intervention": float(w["intervene"].mean()),
                    "latency_p99": float(np.percentile(w["latency_ms"], 99)), "unseen": float(unseen)})
    return out


def slice_table(inf: pd.DataFrame) -> dict:
    """Tasa de intervención y puntuación media por segmento (los mismos que evaluation)."""
    ok = pp.add_row_features(strip_inputs(inf[inf["status"] == "ok"]))
    out = {}
    for col in ["sales_channel", "trip_type", "purchase_lead_bucket"]:
        g = ok.groupby(col).agg(n=("prob_conversion", "size"), score_medio=("prob_conversion", "mean"),
                                intervencion=("intervene", "mean"))
        out[col] = {str(k): {"n": int(r.n), "score_medio": float(r.score_medio), "intervencion": float(r.intervencion)}
                    for k, r in g.iterrows()}
    return out
