#!/usr/bin/env python3
"""Gate `data-contract`: valida el dataset contra los contratos de `<modelo>-data`.

Uso: python gates/data_contract.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import _contracts as C

GATE = "data-contract"


def metrics(df: pd.DataFrame) -> dict:
    return {"null_count": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "row_count": len(df),
            "positive_rate": float(df["booking_complete"].mean())}


def evaluate(df: pd.DataFrame, contract: dict) -> list[dict]:
    m, checks = metrics(df), []
    for a in contract.get("assert", []):
        if "metric" in a:
            v = m[a["metric"]]
            checks.append({"check": f"{a['metric']} {a['op']} {a['value']}", "value": v,
                           "ok": C.compare(v, a["op"], a["value"])})
        elif "range" in a:
            lo, hi = a["range"]
            col = df[a["column"]]
            checks.append({"check": f"{a['column']} in [{lo}, {hi}]", "value": [col.min(), col.max()],
                           "ok": bool(col.between(lo, hi).all())})
        elif "values" in a:
            bad = sorted(set(df[a["column"]].unique()) - set(a["values"]), key=str)
            checks.append({"check": f"{a['column']} in {a['values']}", "value": bad, "ok": not bad})
    return checks


def main() -> int:
    args = C.main_args()
    checks = []
    for c in C.load(args.change, GATE):
        checks += evaluate(pd.read_parquet(c["dataset"]), c)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
