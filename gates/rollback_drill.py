#!/usr/bin/env python3
"""Gate `rollback-drill`: reapuntar un alias cambia la versión servida, en los dos sentidos.

Uso: python gates/rollback_drill.py --change <id>   (desde la raíz del repo)
Usa un alias de prueba (`drill`) para no tocar `champion`.
"""
import sys
from pathlib import Path

from mlflow import MlflowClient

sys.path.insert(0, str(Path(__file__).parent))
for d in ("code/05-evaluation", "code/06-deploy"):
    sys.path.insert(0, str(Path(d).resolve()))
import _contracts as C
import common
import predict as P

GATE = "rollback-drill"
ALIAS = "drill"


def drill(versions: list, name: str = common.REGISTERED_MODEL) -> tuple[list, list]:
    """Apunta el alias a cada versión y sirve un lote; devuelve (versiones servidas, lotes fallidos)."""
    client, served, failed = MlflowClient(), [], []
    try:
        for v in versions:
            client.set_registered_model_alias(name, ALIAS, str(v))
            info = P.resolve(name, None, ALIAS)
            try:
                rec = P.run_inference(P.sample_rows(P.BRONZE, 2, 5), info, out_dir=None)
                served.append(int(rec["model_version"].iloc[0]))
                if not (rec["status"] == "ok").all():
                    failed.append(v)
            except Exception:
                served.append(None)
                failed.append(v)
    finally:
        try:
            client.delete_registered_model_alias(name, ALIAS)
        except Exception:
            pass
    return served, failed


def main() -> int:
    args = C.main_args()
    common.init_mlflow()
    checks = []
    for c in C.load_any(args.change, GATE):
        for a in c["assert"]:
            versions = a.get("versions")
            if a["check"] == "alias_flip_changes_served_version":
                # ida y vuelta: v1 -> v2 -> v1, para probar que revertir es tan directo como avanzar
                seq = list(versions) + [versions[0]]
                served, failed = drill(seq)
                checks.append({"check": a["check"], "sequence": seq, "served": served, "ok": served == seq})
                checks.append({"check": "no_failed_inference", "failed": failed, "ok": not failed})
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
