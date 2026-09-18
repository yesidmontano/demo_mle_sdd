#!/usr/bin/env python3
"""Gate `leakage-check`: fuga en el conjunto de features de train, según `<modelo>-features`.

Uso: python gates/leakage_check.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.

Limitación declarada: sin fecha no detecta fuga temporal sutil, solo columnas
demasiado predictivas por sí solas, columnas prohibidas o filas compartidas entre train y test.
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).parent))
import _contracts as C

GATE = "leakage-check"
TARGET = "booking_complete"


def single_feature_auc(df: pd.DataFrame) -> dict[str, float]:
    """AUC simétrico por feature; las categóricas con target encoding fuera de pliegue."""
    y, out = df[TARGET], {}
    for c in df.columns.drop(TARGET):
        if pd.api.types.is_numeric_dtype(df[c]):
            x = df[c].astype(float)
        else:
            x = pd.Series(index=df.index, dtype=float)
            for tr, te in KFold(5, shuffle=True, random_state=0).split(df):
                means = y.iloc[tr].groupby(df[c].iloc[tr]).mean()
                x.iloc[te] = df[c].iloc[te].map(means).fillna(y.iloc[tr].mean()).values
        auc = roc_auc_score(y, x)
        out[c] = max(auc, 1 - auc)
    return out


def evaluate(train: pd.DataFrame, contract: dict, test: pd.DataFrame | None = None) -> list[dict]:
    checks = []
    for a in contract.get("assert", []):
        m = a["metric"]
        if m == "single_feature_auc":
            aucs = single_feature_auc(train)
            worst = max(aucs, key=aucs.get)
            checks.append({"check": f"single_feature_auc {a['op']} {a['value']}",
                           "value": {worst: round(aucs[worst], 4)},
                           "ok": all(C.compare(v, a["op"], a["value"]) for v in aucs.values())})
        elif m == "forbidden_columns_present":
            found = [c for c in a["forbidden"] if c in train.columns]
            checks.append({"check": "forbidden_columns_present == 0", "value": found, "ok": not found})
        elif m == "split_overlap_rows" and test is not None:
            overlap = len(train.merge(test.drop_duplicates(), how="inner"))
            checks.append({"check": "split_overlap_rows == 0", "value": overlap, "ok": overlap == 0})
    return checks


def main() -> int:
    args = C.main_args()
    checks = []
    for c in C.load(args.change, GATE):
        checks += evaluate(pd.read_parquet(c["train"]), c, pd.read_parquet(c["test"]))
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
