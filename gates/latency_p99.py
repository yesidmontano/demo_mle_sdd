#!/usr/bin/env python3
"""Gate `latency-p99`: latencia por sesión (1 fila, modelo precalentado) de la función de despliegue.

Uso: python gates/latency_p99.py --change <id>   (desde la raíz del repo)
Mide el tiempo completo de `run_inference` (validación + pipeline + predicción), no solo `predict`.
"""
import sys
import time
from pathlib import Path

import numpy as np
from mlflow import MlflowClient

sys.path.insert(0, str(Path(__file__).parent))
for d in ("code/05-evaluation", "code/06-deploy"):
    sys.path.insert(0, str(Path(d).resolve()))
import _contracts as C
import common
import predict as P

GATE = "latency-p99"
WARMUP = 10


def measure(model, info, n: int) -> list[float]:
    rows = P.read_source(P.BRONZE)
    out = []
    for i in range(WARMUP + n):
        one = P.sample_rows(rows, 1, i)
        t0 = time.perf_counter()
        P.run_inference(one, info, model=model, out_dir=None)
        if i >= WARMUP:
            out.append((time.perf_counter() - t0) * 1000)
    return out


def evaluate(lat: list, contract: dict) -> list[dict]:
    a, v = contract["assert"][0], float(np.percentile(lat, 99))
    return [{"check": f"p99_ms {a['op']} {a['value']}", "value": round(v, 2), "p50_ms": round(float(np.median(lat)), 2),
             "sessions": len(lat), "ok": C.compare(v, a["op"], a["value"])}]


def main() -> int:
    args = C.main_args()
    common.init_mlflow()
    mvs = MlflowClient().search_model_versions(f"name='{common.REGISTERED_MODEL}'")
    version = str(max(int(m.version) for m in mvs if m.tags.get("role") == "candidate"))
    info = P.resolve(common.REGISTERED_MODEL, version, None)
    model, _ = P.load(info)
    checks = []
    for c in C.load_any(args.change, GATE):
        checks += evaluate(measure(model, info, c["sessions"]), c)
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
