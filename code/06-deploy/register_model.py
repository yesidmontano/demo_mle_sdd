"""Fase 06 — registra línea base (v1, destino de rollback) y candidato sellado (v2) en el Model Registry.

No asigna alias `champion`: eso lo hace `promote.py`, con comprobante. Escribe también la referencia de
drift (`data/silver/monitoring_reference.json`). Requiere el MLflow local de la fase 04.
Ejecutar desde la raíz: python code/06-deploy/register_model.py
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import mlflow
import numpy as np
from mlflow import MlflowClient

for d in ("gates", "code/05-evaluation", "code/07_operation_and_monitoring"):
    sys.path.insert(0, str(Path(d).resolve()))
import _contracts as C
import common
import drift

ARCHIVED_SEAL = "openspec/changes/archive/*conversion-sesion-modeling-evaluation/evidence/seal.json"


def find_seal() -> Path:
    found = sorted(Path(".").glob(ARCHIVED_SEAL))
    if not found:
        sys.exit("No encuentro el sello del candidato; pásalo con --seal")
    return found[-1]


def k_fraction() -> float:
    """K sale de la spec de evaluation vigente, no del código."""
    return float(next(c["decision"]["k_fraction"] for c in C.load_specs("slice-eval") if "decision" in c))


def artifact_hash(uri: str) -> str:
    return hashlib.sha256(next(Path(mlflow.artifacts.download_artifacts(uri)).glob("model.*")).read_bytes()).hexdigest()


def register(client: MlflowClient, run_id: str, tags: dict) -> str:
    """Registra el run como una versión nueva, o reutiliza la que ya lo tiene (idempotente)."""
    for mv in client.search_model_versions(f"name='{common.REGISTERED_MODEL}'"):
        if mv.tags.get("run_id") == run_id:
            version = mv.version
            break
    else:
        version = mlflow.register_model(f"runs:/{run_id}/model", common.REGISTERED_MODEL).version
    for key, value in tags.items():
        client.set_model_version_tag(common.REGISTERED_MODEL, version, key, str(value))
    return str(version)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seal", type=Path, default=None)
    seal_path = ap.parse_args().seal or find_seal()
    seal = json.loads(seal_path.read_text())

    common.init_mlflow()
    client = MlflowClient()
    if artifact_hash(f"runs:/{seal['run_id']}/model") != seal["identities"]["model"]:
        sys.exit("El artefacto del candidato no coincide con el sello: no se registra")

    k = k_fraction()
    test = common.load_test()
    scores = {role: common.proba(common.load_model(rid), test)
              for role, rid in (("baseline", seal["baseline_run_id"]), ("candidate", seal["run_id"]))}
    versions = {}
    for role, run_id in (("baseline", seal["baseline_run_id"]), ("candidate", seal["run_id"])):
        tags = {"run_id": run_id, "role": role, "k_fraction": k,
                "decision_threshold": round(float(np.quantile(scores[role], 1 - k)), 6)}
        if role == "baseline":
            tags["rollback_target"] = "true"
        versions[role] = register(client, run_id, tags)

    ref = drift.build_reference(common.load_train(), scores["candidate"], k)
    drift.save_reference(ref)
    print(json.dumps({"model": common.REGISTERED_MODEL, "versions": versions, "k_fraction": k,
                      "seal": str(seal_path), "reference": str(drift.REFERENCE_PATH)}))


if __name__ == "__main__":
    main()
