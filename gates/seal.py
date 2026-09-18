#!/usr/bin/env python3
"""Sella el candidato: congela cinco identidades antes de leer ninguna métrica de test.

Uso: python gates/seal.py --change <id> --run-id <candidato> --baseline-run-id <base>
Escribe openspec/changes/<id>/evidence/seal.json. NO sobrescribe un sello existente:
un sello que se puede reescribir no congela nada.
"""
import argparse
import hashlib
import importlib.metadata as md
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import mlflow

TRACKING_URI = "sqlite:///mlflow.db"
ENV_PACKAGES = ["pandas", "numpy", "scikit-learn", "mlflow", "pyarrow", "joblib"]
STORE = Path("data/silver")


def sha(paths) -> str:
    h = hashlib.sha256()
    for p in sorted(Path(x) for x in paths):
        h.update(str(p).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def identities(change: str, run_id: str) -> dict:
    spec_files = [*Path("openspec/specs").glob("conversion-sesion-*/spec.md"),
                  *Path("openspec/changes", change, "specs").glob("*/spec.md")]
    code_files = [*Path("code/03-data_preparation").glob("*.py"), *Path("code/04-modeling").glob("*.py")]
    data_files = [STORE / f"{n}.parquet" for n in ("train", "test", "train_features", "test_features")]
    data_files.append(STORE / "preprocessing_pipeline.joblib")
    env = {"python": platform.python_version(), **{p: md.version(p) for p in ENV_PACKAGES}}
    mlflow.set_tracking_uri(TRACKING_URI)
    model_pkl = next(Path(mlflow.artifacts.download_artifacts(f"runs:/{run_id}/model")).glob("model.*"))
    return {"spec_pack": sha(spec_files), "dataset": sha(data_files), "code": sha(code_files),
            "environment": hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest(),
            "model": hashlib.sha256(model_pkl.read_bytes()).hexdigest(), "environment_detail": env}


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--change", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--baseline-run-id", required=True)
    a = p.parse_args()
    out = Path("openspec/changes", a.change, "evidence", "seal.json")
    if out.exists():
        print(json.dumps({"gate": "seal", "status": "fail", "detail": f"ya existe {out}: un sello no se reescribe"}))
        return 1
    seal = {"change": a.change, "run_id": a.run_id, "baseline_run_id": a.baseline_run_id,
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain")),
            "identities": identities(a.change, a.run_id)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(seal, indent=2))
    print(json.dumps({"gate": "seal", "status": "pass", "run_id": a.run_id, "sealed_at": seal["sealed_at"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
