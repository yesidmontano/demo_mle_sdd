#!/usr/bin/env python3
"""Gate `incumbent-rerun`: reentrenar la línea base desde cero reproduce su log-loss en test.

Uso: python gates/incumbent_rerun.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.
"""
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent))
for d in ("code/05-evaluation", "code/04-modeling"):
    sys.path.insert(0, str(Path(d).resolve()))
import _contracts as C
import common
import preprocessing as pp
import train

GATE = "incumbent-rerun"


def rerun_log_loss() -> float:
    """Reentrena la línea base con el mismo código, datos y semilla, y mide log-loss en test."""
    pre = joblib.load(common.STORE / "preprocessing_pipeline.joblib")
    feats = pd.read_parquet(common.STORE / "train_features.parquet")
    clf = train.make_baseline().fit(feats.drop(columns=[pp.TARGET]), feats[pp.TARGET])
    test = common.load_test()
    return float(log_loss(test[pp.TARGET], common.proba(Pipeline([("prep", pre), ("clf", clf)]), test), labels=[0, 1]))


def evaluate(registered: float, fresh: float, contract: dict) -> list[dict]:
    a, d = contract["assert"][0], abs(registered - fresh)
    return [{"check": f"log_loss_abs_diff {a['op']} {a['value']}", "registered": registered,
             "rerun": fresh, "value": d, "ok": C.compare(d, a["op"], a["value"])}]


def main() -> int:
    args = C.main_args()
    seal = common.load_seal(args.change)
    test = common.load_test()
    registered = float(log_loss(test[pp.TARGET], common.proba(common.load_model(seal["baseline_run_id"]), test), labels=[0, 1]))
    fresh = rerun_log_loss()
    checks = []
    for c in C.load(args.change, GATE):
        checks += evaluate(registered, fresh, c)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
