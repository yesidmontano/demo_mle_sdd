#!/usr/bin/env python3
"""Gate `false-positive-budget`: sin desvío, las alertas de drift no superan el presupuesto.

Uso: python gates/false_positive_budget.py --change <id>   (desde la raíz del repo)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/07_operation_and_monitoring").resolve()))
import _contracts as C
import drift as D

GATE = "false-positive-budget"


def main() -> int:
    args = C.main_args()
    ref, checks = D.load_reference(), []
    for c in C.load_any(args.change, GATE):
        train = pd.read_parquet(c["reference"])
        r = D.backtest(ref, train, c["windows"], c["window_size"], c["seed"], None, c["rule"]["alert_psi"])
        a = c["assert"][0]
        checks.append({"check": f"{a['metric']} {a['op']} {a['value']}", "value": round(r["alert_rate"], 4),
                       "median_max_psi": round(r["median_max_psi"], 3), "windows": c["windows"],
                       "ok": C.compare(r["alert_rate"], a["op"], a["value"])})
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
