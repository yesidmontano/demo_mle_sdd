"""Fase 07 — genera el dashboard HTML autocontenido desde `data/gold/inferences/`.

Un HTML abierto desde file:// no puede leer Parquet ni hacer fetch a archivos locales, así que la
«conexión» con Gold es este paso de construcción: lee las inferencias, calcula señales con `drift.py`
(la misma lógica que los gates de alertas) e incrusta el resultado en la plantilla. Para refrescar,
vuelve a ejecutarlo:

  python code/07_operation_and_monitoring/build_dashboard.py
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import drift as D

INFERENCES = Path("data/gold/inferences")
TEMPLATE = Path(__file__).parent / "dashboard_template.html"
OUT = Path("results/07_operation_and_monitoring/dashboard.html")
RANGES = {"all": None, "7d": timedelta(days=7), "3d": timedelta(days=3), "24h": timedelta(hours=24)}
SOURCES = ["all", "cli", "simulation"]
BUCKETS = [timedelta(hours=h) for h in (1, 3, 6, 12, 24)]


def load(path: Path) -> pd.DataFrame:
    files = sorted(path.glob("inferences_*.parquet"))
    if not files:
        sys.exit(f"No hay inferencias en {path}/. Ejecuta code/06-deploy/predict.py o simulate_traffic.py")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)


def clean(o):
    """JSON seguro: NaN/NA a null, tipos numpy a nativos."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if o is pd.NA or o is pd.NaT:
        return None
    return o


def bucketed(inf: pd.DataFrame) -> dict:
    span = inf["timestamp_utc"].max() - inf["timestamp_utc"].min()
    step = next((b for b in BUCKETS if span / b <= 48), BUCKETS[-1])
    grp = inf.groupby(inf["timestamp_utc"].dt.floor(step))
    ok = inf[inf["status"] == "ok"].groupby(inf["timestamp_utc"].dt.floor(step))
    t = list(grp.size().index)
    lat = lambda q: [float(np.percentile(ok.get_group(k)["latency_ms"], q)) if k in ok.groups else None for k in t]
    return {"bucket_hours": step.total_seconds() / 3600, "t": [x.isoformat() for x in t],
            "volume": grp.size().tolist(), "rejected": [int((g["status"] != "ok").sum()) for _, g in grp],
            "latency_p50": lat(50), "latency_p99": lat(99)}


def score_hist(inf: pd.DataFrame, ref: dict) -> dict | None:
    ok = inf[inf["status"] == "ok"].tail(D.WINDOW)
    edges = ref["score"]["edges"]
    labels = [f"< {edges[0]:.2f}"] + [f"{a:.2f}–{b:.2f}" for a, b in zip(edges[:-1], edges[1:])] + [f"≥ {edges[-1]:.2f}"]
    cur = None
    if len(ok) >= D.WINDOW:
        idx = np.searchsorted(edges, ok["prob_conversion"].to_numpy(), side="right")
        cur = (np.bincount(idx, minlength=len(edges) + 1) / len(ok)).tolist()
    return {"labels": labels, "ref": ref["score"]["freq"], "cur": cur}


def build_view(inf: pd.DataFrame, ref: dict) -> dict:
    if inf.empty:
        return {"empty": True}
    sig = D.signals(inf, ref)
    versions = (inf.groupby(["model_version", "model_run_id"]).size().reset_index(name="n")
                .sort_values("model_version", ascending=False))
    recent = inf.tail(12).iloc[::-1]
    return {
        "empty": False, "n": len(inf), "n_ok": int((inf["status"] == "ok").sum()),
        "n_rejected": int((inf["status"] != "ok").sum()),
        "first": inf["timestamp_utc"].min().isoformat(), "last": inf["timestamp_utc"].max().isoformat(),
        "signals": sig, "psi_by_feature": next((s["detail"].get("por_feature") for s in sig if s["name"] == "psi_features"), None),
        "rolling": D.rolling_psi(inf, ref), "series": bucketed(inf), "score_hist": score_hist(inf, ref),
        "slices": D.slice_table(inf),
        "versions": [{"version": int(r.model_version), "run_id": r.model_run_id, "n": int(r.n), "share": r.n / len(inf)}
                     for r in versions.itertuples()],
        "recent": [{"ts": r.timestamp_utc.isoformat(), "version": int(r.model_version), "source": r.source,
                    "prob": r.prob_conversion, "intervene": None if pd.isna(r.intervene) else bool(r.intervene),
                    "latency": r.latency_ms, "status": r.status, "route": r.in_route, "channel": r.in_sales_channel}
                   for r in recent.itertuples()],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inferences", type=Path, default=INFERENCES)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    inf, ref = load(a.inferences), D.load_reference()
    views = {}
    for rkey, delta in RANGES.items():
        cut = inf[inf["timestamp_utc"] >= inf["timestamp_utc"].max() - delta] if delta else inf
        for skey in SOURCES:
            views[f"{rkey}|{skey}"] = build_view(cut if skey == "all" else cut[cut["source"] == skey], ref)
    data = {"generated_at": datetime.now(timezone.utc).isoformat(), "source_dir": str(a.inferences),
            "window": D.WINDOW, "k_fraction": ref["k_fraction"], "views": views,
            "sources_present": sorted(inf["source"].unique().tolist())}
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(clean(data), ensure_ascii=False))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(html, encoding="utf-8")
    print(f"{a.out}  ({len(inf)} inferencias · {a.out.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
