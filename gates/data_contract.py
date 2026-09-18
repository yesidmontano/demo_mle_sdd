#!/usr/bin/env python3
"""Gate `data-contract`: valida datasets y feature store contra los contratos de `<modelo>-data`.

Uso: python gates/data_contract.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import _contracts as C

GATE = "data-contract"
DATA_FILES = {".parquet", ".csv"}


def metrics(df: pd.DataFrame) -> dict:
    return {"null_count": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "row_count": len(df),
            "positive_rate": float(df["booking_complete"].mean())}


def evaluate(df: pd.DataFrame, contract: dict, label: str = "") -> list[dict]:
    """Aserciones de esquema sobre un DataFrame."""
    m, checks = metrics(df), []
    tag = f"[{label}] " if label else ""
    for a in contract.get("assert", []):
        if "metric" in a:
            v = m[a["metric"]]
            checks.append({"check": f"{tag}{a['metric']} {a['op']} {a['value']}", "value": v,
                           "ok": C.compare(v, a["op"], a["value"])})
        elif "range" in a:
            lo, hi = a["range"]
            col = df[a["column"]]
            checks.append({"check": f"{tag}{a['column']} in [{lo}, {hi}]", "value": [col.min(), col.max()],
                           "ok": bool(col.between(lo, hi).all())})
        elif "values" in a:
            bad = sorted(set(df[a["column"]].unique()) - set(a["values"]), key=str)
            checks.append({"check": f"{tag}{a['column']} in {a['values']}", "value": bad, "ok": not bad})
    return checks


def split_metrics(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    overlap = len(train.merge(test.drop_duplicates(), how="inner"))
    return {"split_positive_rate_gap": abs(float(train["booking_complete"].mean() - test["booking_complete"].mean())),
            "split_overlap_rows": overlap,
            "test_fraction": len(test) / (len(train) + len(test))}


def evaluate_store(contract: dict, gold_dir: Path = Path("data/gold")) -> list[dict]:
    """Aserciones sobre el feature store: archivos, split y gold vacía."""
    checks = []
    m = {}
    if "train" in contract:
        m = split_metrics(pd.read_parquet(contract["train"]), pd.read_parquet(contract["test"]))
    m["gold_data_files"] = len([p for p in gold_dir.glob("*") if p.suffix in DATA_FILES | {".joblib"}])
    for a in contract.get("assert", []):
        if a["metric"] == "files_present":
            missing = [f for f in a["value"] if not Path(f).exists()]
            checks.append({"check": "files_present", "value": missing, "ok": not missing})
        else:
            v = m[a["metric"]]
            checks.append({"check": f"{a['metric']} {a['op']} {a['value']}", "value": v,
                           "ok": C.compare(v, a["op"], a["value"])})
    return checks


def main() -> int:
    args = C.main_args()
    checks = []
    for c in C.load(args.change, GATE):
        paths = c.get("datasets") or ([c["dataset"]] if "dataset" in c else [])
        if paths:
            for p in paths:
                checks += evaluate(pd.read_parquet(p), c, label=Path(p).name)
        else:
            checks += evaluate_store(c)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
