"""Fase 06 — despliegue simulado en local: sirve sesiones con una versión registrada y guarda las inferencias.

  python code/06-deploy/predict.py                          # 3 sesiones al azar, alias `champion`
  python code/06-deploy/predict.py --model-version 1        # otra versión del modelo registrado
  python code/06-deploy/predict.py --n-rows 2 --seed 7      # lote reproducible

Cada inferencia queda en data/gold/inferences/ (un Parquet por lote) con la versión y el run_id del modelo,
la probabilidad, la decisión, la latencia y las ENTRADAS (prefijo `in_`), que sirven para medir data drift.
"""
import argparse
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient

sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
import common
import preprocessing as pp

BRONZE = Path("data/bronze/customer_booking.csv")
OUT_DIR = Path("data/gold/inferences")
INT_COLS = ["num_passengers", "purchase_lead", "length_of_stay", "flight_hour", *pp.WANTS]
FLOAT_COLS = ["flight_duration"]
STR_COLS = ["sales_channel", "trip_type", "flight_day", "route", "booking_origin"]
IN = "in_"
DEFAULT_ALIAS = "champion"


def read_source(source: Path) -> pd.DataFrame:
    return pd.read_parquet(source) if source.suffix == ".parquet" else pd.read_csv(source, encoding="latin1")


def sample_rows(source, n: int, seed: int | None, weights_col: tuple | None = None) -> pd.DataFrame:
    """`n` sesiones al azar del dataset crudo (ruta o DataFrame), sin el objetivo. `source_row_index` = fila de origen."""
    df = source if isinstance(source, pd.DataFrame) else read_source(source)
    w = None
    if weights_col:                                   # solo lo usa el simulador para inyectar desvío
        col, value, factor = weights_col
        w = np.where(df[col].astype(str) == value, float(factor), 1.0)
    picked = df.sample(n=n, random_state=seed, weights=w)
    out = picked[pp.INPUT_COLUMNS].copy()
    out.insert(0, "source_row_index", picked.index.to_numpy())
    return out.reset_index(drop=True)


def resolve(model_name: str, version: str | None, alias: str | None) -> dict:
    """Versión registrada elegida: por número o por alias."""
    client = MlflowClient()
    mv = (client.get_model_version(model_name, version) if version
          else client.get_model_version_by_alias(model_name, alias or DEFAULT_ALIAS))
    return {"name": model_name, "version": str(mv.version), "alias": None if version else (alias or DEFAULT_ALIAS),
            "run_id": mv.tags.get("run_id"), "threshold": float(mv.tags["decision_threshold"]),
            "k_fraction": float(mv.tags["k_fraction"])}


def load(info: dict):
    t0 = time.perf_counter()
    model = mlflow.pyfunc.load_model(f"models:/{info['name']}/{info['version']}")
    return model, (time.perf_counter() - t0) * 1000


def reject_reasons(df: pd.DataFrame) -> pd.Series:
    """Motivo de rechazo por fila (cadena vacía = válida): campo ausente o valor no convertible al tipo."""
    reasons = pd.Series("", index=df.index)
    for c in pp.INPUT_COLUMNS:
        if c not in df.columns:
            reasons[:] = f"columna ausente: {c}"
            return reasons
    for c in pp.INPUT_COLUMNS:
        bad = df[c].isna() | (df[c].astype(str).str.strip() == "")
        if c in INT_COLS + FLOAT_COLS:
            bad |= pd.to_numeric(df[c], errors="coerce").isna()
        reasons = reasons.mask(bad & (reasons == ""), f"valor ausente o inválido: {c}")
    return reasons


def typed_inputs(df: pd.DataFrame) -> pd.DataFrame:
    """Entradas con tipos nulables estables, para que todos los lotes tengan el mismo esquema."""
    out = pd.DataFrame(index=df.index)
    for c in pp.INPUT_COLUMNS:
        s = df[c] if c in df.columns else pd.Series(pd.NA, index=df.index)
        if c in INT_COLS:
            out[f"{IN}{c}"] = pd.to_numeric(s, errors="coerce").astype("Int64")
        elif c in FLOAT_COLS:
            out[f"{IN}{c}"] = pd.to_numeric(s, errors="coerce").astype("Float64")
        else:
            out[f"{IN}{c}"] = s.astype("string")
    return out


def run_inference(rows: pd.DataFrame, info: dict, model=None, model_load_ms=None, out_dir: Path | None = OUT_DIR,
                  source: str = "cli", timestamp: datetime | None = None, seed: int | None = None) -> pd.DataFrame:
    """Sirve un lote: valida, predice con el pipeline completo, y guarda un Parquet si `out_dir` no es None."""
    if model is None:
        model, model_load_ms = load(info)
    ts = timestamp or datetime.now(timezone.utc)
    reasons = reject_reasons(rows)
    valid = rows[reasons == ""]
    prob, latency = pd.Series(np.nan, index=rows.index), np.nan
    if len(valid):
        x = valid[pp.INPUT_COLUMNS].copy()
        for c in INT_COLS:
            x[c] = pd.to_numeric(x[c]).astype("int64")
        for c in FLOAT_COLS:
            x[c] = pd.to_numeric(x[c]).astype("float64")
        for c in STR_COLS:
            x[c] = x[c].astype(str)
        t0 = time.perf_counter()
        p = np.asarray(model.predict(x))[:, 1]
        latency = (time.perf_counter() - t0) * 1000 / len(valid)      # ms por sesión
        prob.loc[valid.index] = p
    batch_id = uuid.uuid4().hex[:8]
    rec = pd.DataFrame({
        "inference_id": [uuid.uuid4().hex for _ in range(len(rows))], "batch_id": batch_id,
        "timestamp_utc": pd.Timestamp(ts), "source": source, "model_name": info["name"],
        "model_version": int(info["version"]), "model_alias": info["alias"], "model_run_id": info["run_id"],
        "prob_conversion": prob.astype("float64"),
        "decision_threshold": info["threshold"], "latency_ms": latency, "model_load_ms": model_load_ms,
        "batch_size": len(rows), "seed": seed, "source_row_index": rows.get("source_row_index"),
        "status": np.where(reasons == "", "ok", "rejected"), "reject_reason": np.where(reasons == "", None, reasons),
    })
    rec["intervene"] = pd.array(np.where(rec["prob_conversion"].isna(), pd.NA, rec["prob_conversion"] >= info["threshold"]),
                                dtype="boolean")
    for c in ("model_alias", "reject_reason"):
        rec[c] = rec[c].astype("string")
    rec["source_row_index"] = rec["source_row_index"].astype("Int64")
    rec["seed"] = pd.array([seed] * len(rec), dtype="Int64")
    rec["model_load_ms"] = pd.array([model_load_ms] * len(rec), dtype="Float64")
    rec = pd.concat([rec, typed_inputs(rows)], axis=1)
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        rec.to_parquet(out_dir / f"inferences_{ts:%Y%m%dT%H%M%S}_{batch_id}.parquet", index=False)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--model-version", help="versión del modelo registrado (p. ej. 2)")
    g.add_argument("--model-alias", help=f"alias del modelo registrado (por defecto {DEFAULT_ALIAS})")
    ap.add_argument("--model-name", default=common.REGISTERED_MODEL)
    ap.add_argument("--n-rows", type=int, default=3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--source", type=Path, default=BRONZE)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    a = ap.parse_args()

    common.init_mlflow()
    info = resolve(a.model_name, a.model_version, a.model_alias)
    rows = sample_rows(a.source, a.n_rows, a.seed)
    rec = run_inference(rows, info, out_dir=a.out, seed=a.seed)
    print(f"modelo {info['name']} v{info['version']} (run {info['run_id'][:8]}) · umbral {info['threshold']:.3f}")
    cols = ["inference_id", "status", "prob_conversion", "intervene", "latency_ms", "in_sales_channel",
            "in_purchase_lead", "in_route"]
    print(rec[cols].assign(inference_id=rec["inference_id"].str[:8]).to_string(index=False))
    print(f"guardado en {a.out}/")


if __name__ == "__main__":
    main()
