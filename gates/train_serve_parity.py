#!/usr/bin/env python3
"""Gate `train-serve-parity`: el pipeline guardado reproduce las features desde los datos crudos.

Uso: python gates/train_serve_parity.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.

Carga el joblib tal como lo haría serving. Requiere `code/03-data_preparation` en el path
para resolver las funciones del pipeline.
"""
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/03-data_preparation").resolve()))
import _contracts as C

GATE = "train-serve-parity"
TARGET = "booking_complete"


def max_abs_diff(pipeline, raw: pd.DataFrame, expected: pd.DataFrame) -> float:
    got = pipeline.transform(raw[list(pipeline.feature_names_in_)])
    exp = expected.drop(columns=[TARGET])
    if list(got.columns) != list(exp.columns):
        return float("inf")
    return float(np.abs(got.to_numpy(float) - exp.to_numpy(float)).max())


def evaluate(pipeline, raw: pd.DataFrame, expected: pd.DataFrame, contract: dict) -> list[dict]:
    d = max_abs_diff(pipeline, raw, expected)
    a = contract["assert"][0]
    return [{"check": f"max_abs_diff {a['op']} {a['value']}", "value": d, "ok": C.compare(d, a["op"], a["value"])}]


def main() -> int:
    args = C.main_args()
    checks = []
    for c in C.load(args.change, GATE):
        checks += evaluate(joblib.load(c["pipeline"]), pd.read_parquet(c["raw"]),
                           pd.read_parquet(c["transformed"]), c)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
