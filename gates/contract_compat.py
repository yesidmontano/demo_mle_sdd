#!/usr/bin/env python3
"""Gate `contract-compat`: el servicio cumple el contrato de `<modelo>-serving`.

Uso: python gates/contract_compat.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea. Requiere el MLflow local y el modelo registrado.
"""
import sys
import tempfile
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient

sys.path.insert(0, str(Path(__file__).parent))
for d in ("code/05-evaluation", "code/06-deploy"):
    sys.path.insert(0, str(Path(d).resolve()))
import _contracts as C
import common
import predict as P
import preprocessing as pp
import receipt as R

GATE = "contract-compat"


def candidate_version() -> str:
    mvs = MlflowClient().search_model_versions(f"name='{common.REGISTERED_MODEL}'")
    return str(max((int(m.version) for m in mvs if m.tags.get("role") == "candidate")))


def sample(n=3, seed=1) -> pd.DataFrame:
    return P.sample_rows(P.BRONZE, n, seed)


def check_receipt_mechanism() -> dict:
    """La promoción debe rechazar comprobantes ausentes, alterados o con gates en rojo, y aceptar uno completo."""
    tags = {"run_id": "r1"}
    good = {"registered_version": "2", "run_id": "r1", "identities": {i: "h" for i in R.IDENTITIES} | {"model": "m"},
            "gates": {g: "pass" for g in R.EVAL_GATES + R.DEPLOY_GATES}}
    bad_hash = R.validate(good, tags, "otro", "2")
    bad_gate = R.validate({**good, "gates": {**good["gates"], "latency-p99": "fail"}}, tags, "m", "2")
    missing_id = R.validate({**good, "identities": {**good["identities"], "code": ""}}, tags, "m", "2")
    ok = bool(R.validate({}, tags, "m", "2") and bad_hash and bad_gate and missing_id and not R.validate(good, tags, "m", "2"))
    return {"check": "promotion_receipt_valid", "ok": ok}


def run_check(a: dict, models: dict, version: str) -> list[dict]:
    name = a["check"]
    if name == "version_selectable":
        out = []
        for v in a["versions"]:
            info = P.resolve(common.REGISTERED_MODEL, str(v), None)
            rec = P.run_inference(sample(), info, model=models[str(v)], out_dir=None)
            out.append({"check": f"version_selectable v{v}", "ok": bool((rec["model_version"] == v).all()
                        and (rec["model_run_id"] == info["run_id"]).all() and rec["model_run_id"].notna().all())})
        return out
    if name == "default_alias":
        return [{"check": name, "value": P.DEFAULT_ALIAS, "ok": P.DEFAULT_ALIAS == a["value"]}]
    if name == "signature_matches_spec":
        sig = mlflow.models.get_model_info(f"models:/{common.REGISTERED_MODEL}/{version}").signature
        got = {i.name: str(i.type).split(".")[-1] for i in sig.inputs.inputs}
        return [{"check": name, "ok": got == a["inputs"], "detail": {k: (got.get(k), v) for k, v in a["inputs"].items() if got.get(k) != v}}]
    if name == "invalid_row_rejected_batch_continues":
        rows = sample(4, 3)
        rows.loc[1, "route"] = None
        rec = P.run_inference(rows, P.resolve(common.REGISTERED_MODEL, version, None), model=models[version], out_dir=None)
        ok = (list(rec["status"]) == ["ok", "rejected", "ok", "ok"] and "route" in str(rec["reject_reason"].iloc[1])
              and rec.loc[rec["status"] == "ok", "prob_conversion"].notna().all() and pd.isna(rec["prob_conversion"].iloc[1]))
        return [{"check": name, "ok": bool(ok)}]
    if name in ("record_columns_present", "inputs_stored_with_prefix"):
        with tempfile.TemporaryDirectory() as d:
            P.run_inference(sample(), P.resolve(common.REGISTERED_MODEL, version, None), model=models[version], out_dir=Path(d))
            files = list(Path(d).glob("*.parquet"))
            df = pd.read_parquet(files[0]) if files else pd.DataFrame()
        cols = a["value"] if name == "record_columns_present" else [f"{a['prefix']}{c}" for c in pp.INPUT_COLUMNS]
        missing = [c for c in cols if c not in df.columns]
        nulls = [c for c in cols if c in df.columns and df[c].isna().any()]
        return [{"check": name, "ok": bool(files) and len(df) == 3 and not missing and not nulls, "missing": missing, "nulls": nulls}]
    if name == "threshold_matches_k":
        tags = MlflowClient().get_model_version(common.REGISTERED_MODEL, version).tags
        p = common.proba(common.load_model(tags["run_id"]), common.load_test())
        frac = float((p >= float(tags["decision_threshold"])).mean())
        return [{"check": name, "value": round(frac, 4), "ok": abs(frac - a["k_fraction"]) <= a["tolerance"]}]
    if name == "promotion_receipt_valid":
        return [check_receipt_mechanism()]
    return [{"check": name, "ok": False, "detail": "comprobación desconocida"}]


def main() -> int:
    args = C.main_args()
    common.init_mlflow()
    version = candidate_version()
    models = {}
    for c in C.load_any(args.change, GATE):
        for a in c.get("assert", []):
            for v in [str(x) for x in a.get("versions", [])] + [version]:
                if v not in models:
                    models[v] = P.load(P.resolve(common.REGISTERED_MODEL, v, None))[0]
    checks = []
    for c in C.load_any(args.change, GATE):
        for a in c.get("assert", []):
            checks += run_check(a, models, version)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
