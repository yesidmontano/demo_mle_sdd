#!/usr/bin/env python3
"""Gate `slice-eval`: candidato sellado vs línea base, global y por segmento, más calibración.

Uso: python gates/slice_eval.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.

Recalcula todo desde los modelos de MLflow; no confía en ningún archivo de resultados.
"""
import hashlib
import sys
from pathlib import Path

import mlflow
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
import _contracts as C
import common

GATE = "slice-eval"


def judge(cand: dict, base: dict, contracts: list[dict]) -> list[dict]:
    """Aplica los umbrales de la spec. `cand`/`base`: {'global': {...}, 'slices': {col: {val: {...}}}}."""
    checks = []
    for c in contracts:
        for a in c.get("assert", []):
            if "metric" not in a:
                continue
            m, op, rel, tol = a["metric"], a["op"], a.get("relative_to_baseline", False), a.get("tolerance", 0.0)
            if a["scope"] == "global":
                v = cand["global"][m]
                target = base["global"][m] + tol if rel else a["value"]
                checks.append({"check": f"global {m} {op} {'baseline%+g' % tol if rel else target}",
                               "candidate": round(v, 5), "reference": round(target, 5), "ok": C.compare(v, op, target)})
            else:
                for col, vals in cand["slices"].items():
                    for val, sm in vals.items():
                        if val not in base["slices"].get(col, {}):
                            continue
                        target = base["slices"][col][val][m] + tol
                        checks.append({"check": f"slice {col}={val} {m} {op} baseline{tol:+g}",
                                       "candidate": round(sm[m], 5), "reference": round(target, 5),
                                       "ok": C.compare(sm[m], op, target)})
    return checks


def seal_checks(change: str, seal: dict, wanted: list[str]) -> list[dict]:
    common.init_mlflow()
    uri = f"runs:/{seal['run_id']}/model"
    out = []
    for name in wanted:
        if name == "model_hash_matches_seal":
            f = next(Path(mlflow.artifacts.download_artifacts(uri)).glob("model.*"))
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            out.append({"check": name, "ok": h == seal["identities"]["model"]})
        elif name == "mlflow_signature_present":
            out.append({"check": name, "ok": mlflow.models.get_model_info(uri).signature is not None})
        elif name == "sealed_before_test_metrics":
            exp = mlflow.get_experiment_by_name(common.EXPERIMENT)
            runs = mlflow.search_runs([exp.experiment_id], filter_string="tags.phase = 'evaluation'", output_format="pandas")
            sealed = pd.Timestamp(seal["sealed_at"])
            ok = len(runs) > 0 and bool((pd.to_datetime(runs["start_time"], utc=True) > sealed).all())
            out.append({"check": name, "ok": ok, "detail": f"{len(runs)} runs de evaluación"})
    return out


def main() -> int:
    args = C.main_args()
    contracts = C.load(args.change, GATE)
    k = float(next(c["decision"]["k_fraction"] for c in contracts if "decision" in c))
    seal = common.load_seal(args.change)
    checks = []
    for c in contracts:
        if "seal" in c:
            checks += seal_checks(args.change, seal, [a["check"] for a in c["assert"]])
    s = common.score(args.change, k)
    checks += judge(s["candidate"], s["baseline"], contracts)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
