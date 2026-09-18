"""Asigna el alias `champion` a una versión registrada. Rollback = promover la versión anterior.

  python code/06-deploy/promote.py --version 2      # requiere comprobante válido
  python code/06-deploy/promote.py --version 1      # rollback: v1 está marcada `rollback_target`
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient

for d in ("gates", "code/05-evaluation"):
    sys.path.insert(0, str(Path(d).resolve()))
import common
import receipt as R

DEFAULT_RECEIPT = "openspec/changes/*conversion-sesion-deploy-monitoring/evidence/receipt.json"


def find_receipt() -> Path | None:
    found = sorted(Path(".").glob(DEFAULT_RECEIPT)) + sorted(Path(".").glob("openspec/changes/archive/" + DEFAULT_RECEIPT.split("/", 2)[2]))
    return found[0] if found else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--alias", default="champion")
    ap.add_argument("--receipt", type=Path, default=None)
    a = ap.parse_args()
    common.init_mlflow()
    client = MlflowClient()
    tags = client.get_model_version(common.REGISTERED_MODEL, a.version).tags

    if tags.get("rollback_target") != "true":
        path = a.receipt or find_receipt()
        art = Path(mlflow.artifacts.download_artifacts(f"models:/{common.REGISTERED_MODEL}/{a.version}"))
        sha = hashlib.sha256(next(art.glob("model.*")).read_bytes()).hexdigest()
        why = R.validate(json.loads(path.read_text()) if path and path.exists() else {}, tags, sha, a.version)
        if why:
            print(json.dumps({"status": "rechazada", "why": why}, ensure_ascii=False))
            return 1
    client.set_registered_model_alias(common.REGISTERED_MODEL, a.alias, a.version)
    print(json.dumps({"status": "ok", "alias": a.alias, "version": a.version, "run_id": tags.get("run_id")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
