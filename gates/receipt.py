#!/usr/bin/env python3
"""Comprobante de promoción: liga las cinco identidades del candidato y prueba que sus gates pasaron.

Uso: python gates/receipt.py --change <id> --version <N> [--seal <ruta>] [--eval-evidence <dir>]
Escribe openspec/changes/<id>/evidence/receipt.json. Código 0 si se emite, 1 si algún requisito falla.
El comprobante es el objeto de promoción, no un permiso: sin él `promote.py` no asigna `champion`.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

IDENTITIES = ["spec_pack", "dataset", "code", "environment", "model"]
EVAL_GATES = ["slice-eval", "behavioral-tests", "incumbent-rerun"]
DEPLOY_GATES = ["contract-compat", "latency-p99", "rollback-drill", "alert-backtest", "false-positive-budget"]


def validate(receipt: dict, version_tags: dict, model_sha: str, version: str) -> list[str]:
    """Motivos por los que un comprobante NO autoriza promover `version` (lista vacía = válido)."""
    why = []
    if not receipt:
        return ["no hay comprobante"]
    for i in IDENTITIES:
        if not receipt.get("identities", {}).get(i):
            why.append(f"falta la identidad {i}")
    if str(receipt.get("registered_version")) != str(version):
        why.append("el comprobante es de otra versión")
    if receipt.get("run_id") != version_tags.get("run_id"):
        why.append("el run_id no coincide con el de la versión registrada")
    if receipt.get("identities", {}).get("model") != model_sha:
        why.append("el hash del modelo no coincide con el artefacto registrado")
    bad = [g for g, s in receipt.get("gates", {}).items() if s != "pass"]
    missing = [g for g in EVAL_GATES + DEPLOY_GATES if g not in receipt.get("gates", {})]
    if bad:
        why.append(f"gates que no pasan: {bad}")
    if missing:
        why.append(f"gates ausentes: {missing}")
    return why


def status_of(path: Path) -> str:
    return json.loads(path.read_text())["status"] if path.exists() else "missing"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--seal", type=Path)
    ap.add_argument("--eval-evidence", type=Path)
    a = ap.parse_args()
    root = Path("openspec/changes/archive")
    seal_path = a.seal or sorted(root.glob("*conversion-sesion-modeling-evaluation/evidence/seal.json"))[-1]
    eval_dir = a.eval_evidence or seal_path.parent
    deploy_dir = Path("openspec/changes", a.change, "evidence")
    seal = json.loads(seal_path.read_text())

    sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
    import common
    import mlflow
    common.init_mlflow()
    tags = mlflow.MlflowClient().get_model_version(common.REGISTERED_MODEL, a.version).tags
    art = Path(mlflow.artifacts.download_artifacts(f"models:/{common.REGISTERED_MODEL}/{a.version}"))
    model_sha = hashlib.sha256(next(art.glob("model.*")).read_bytes()).hexdigest()

    gates = {g: status_of(eval_dir / f"{g}.json") for g in EVAL_GATES}
    gates |= {g: status_of(deploy_dir / f"{g}.json") for g in DEPLOY_GATES}
    receipt = {"change": a.change, "registered_model": common.REGISTERED_MODEL, "registered_version": a.version,
               "run_id": seal["run_id"], "created_at": datetime.now(timezone.utc).isoformat(),
               "identities": {i: seal["identities"][i] for i in IDENTITIES}, "gates": gates,
               "seal": str(seal_path), "sealed_at": seal["sealed_at"]}
    why = validate(receipt, tags, model_sha, a.version)
    if why:
        print(json.dumps({"gate": "receipt", "status": "fail", "why": why}, ensure_ascii=False))
        return 1
    (deploy_dir / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({"gate": "receipt", "status": "pass", "version": a.version, "run_id": receipt["run_id"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
