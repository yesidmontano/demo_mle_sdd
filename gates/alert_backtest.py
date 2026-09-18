#!/usr/bin/env python3
"""Gate `alert-backtest`: la regla de alertas detecta un desvío real y el dashboard cumple la spec.

Uso: python gates/alert_backtest.py --change <id>   (desde la raíz del repo)
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/07_operation_and_monitoring").resolve()))
import _contracts as C
import drift as D

GATE = "alert-backtest"
EXTERNAL = re.compile(r"""(src|href)\s*=\s*["']?(https?:)?//(?!www\.w3\.org)|url\(\s*["']?(https?:)?//|@import|<link[^>]+rel=["']?stylesheet""", re.I)


def synthetic_inferences(n=260) -> pd.DataFrame:
    """Inferencias sintéticas con el esquema real, solo para comprobar que el resumen emite todo."""
    train = pd.read_parquet("data/silver/train.parquet").sample(n, random_state=1).reset_index(drop=True)
    inf = train[D.pp.INPUT_COLUMNS].rename(columns=lambda c: f"{D.IN}{c}")
    rng = np.random.default_rng(1)
    inf["prob_conversion"] = rng.random(n)
    inf["intervene"] = inf["prob_conversion"] >= 0.8
    inf["latency_ms"] = rng.random(n) * 30
    inf["status"] = "ok"
    inf["timestamp_utc"] = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    return inf


def run_check(a: dict, c: dict, ref: dict) -> list[dict]:
    if "metric" in a:
        train = pd.read_parquet(c["reference"])
        r = D.backtest(ref, train, c["windows"], c["window_size"], c["seed"], c.get("drift_scenario"))
        v = r["alert_rate"]
        return [{"check": f"{a['metric']} {a['op']} {a['value']}", "value": round(v, 4),
                 "median_max_psi": round(r["median_max_psi"], 3), "ok": C.compare(v, a["op"], a["value"])}]
    name = a["check"]
    if name == "signals_present":
        got = [s["name"] for s in D.signals(synthetic_inferences(), ref)]
        return [{"check": name, "missing": [s for s in a["value"] if s not in got], "ok": all(s in got for s in a["value"])}]
    if name == "slices_present":
        got = list(D.slice_table(synthetic_inferences()))
        return [{"check": name, "missing": [s for s in a["value"] if s not in got], "ok": all(s in got for s in a["value"])}]
    if name in ("dashboard_offline", "dashboard_panels"):
        path = Path(c["dashboard"])
        if not path.exists():
            return [{"check": name, "ok": False, "detail": f"no existe {path}"}]
        html = path.read_text(encoding="utf-8")
        if name == "dashboard_offline":
            return [{"check": name, "ok": not EXTERNAL.search(html)}]
        # el DOM se construye en JS: el panel debe declararse como `card("<panel>"` o `"data-panel": "<panel>"`
        declared = lambda p: re.search(rf"""(card\(|data-panel["']?\s*[:=]\s*)["']{p}["']""", html)
        missing = [p for p in a["value"] if not declared(p)]
        return [{"check": name, "missing": missing, "ok": not missing}]
    return [{"check": name, "ok": False, "detail": "comprobación desconocida"}]


def main() -> int:
    args = C.main_args()
    ref = D.load_reference()
    checks = []
    for c in C.load_any(args.change, GATE):
        for a in c.get("assert", []):
            checks += run_check(a, c, ref)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
