#!/usr/bin/env python3
"""Gate `behavioral-tests`: el candidato sellado se comporta de forma coherente.

Uso: python gates/behavioral_tests.py --change <id>   (desde la raíz del repo)
Salida: JSON en stdout; código 0 pasa, 1 bloquea.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
import _contracts as C
import common
import preprocessing as pp

GATE = "behavioral-tests"
SAMPLE = 2000


def run_tests(model, raw, names_tol: dict) -> list[dict]:
    sample = raw.sample(min(SAMPLE, len(raw)), random_state=pp.SEED).reset_index(drop=True)
    x = sample[pp.INPUT_COLUMNS]
    out = []
    for name, tol in names_tol.items():
        try:
            if name == "probabilities_valid":
                p = model.predict_proba(x)
                ok = bool(np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all()
                          and np.allclose(p.sum(axis=1), 1.0, atol=1e-6) and p.shape == (len(x), 2))
                detail = {"shape": list(p.shape)}
            elif name == "unseen_category_tolerated":
                u = x.copy()
                u["booking_origin"], u["route"] = "Atlantis", "XXXYYY"
                p = model.predict_proba(u)
                ok, detail = bool(np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all()), {}
            elif name == "wants_flags_directional":
                off, on = x.copy(), x.copy()
                off[pp.WANTS], on[pp.WANTS] = 0, 1
                delta = float(model.predict_proba(on)[:, 1].mean() - model.predict_proba(off)[:, 1].mean())
                ok, detail = delta >= tol, {"mean_delta": round(delta, 5)}
            else:
                ok, detail = False, {"error": "prueba desconocida"}
        except Exception as e:   # una prueba que revienta es una prueba que falla
            ok, detail = False, {"error": repr(e)}
        out.append({"check": name, "ok": ok, **detail})
    return out


def main() -> int:
    args = C.main_args()
    seal = common.load_seal(args.change)
    model = common.load_model(seal["run_id"])
    raw = common.load_test()
    checks = []
    for c in C.load(args.change, GATE):
        checks += run_tests(model, raw, {a["test"]: a.get("tolerance", 0.0) for a in c["assert"]})
    return C.finish(GATE, args.change, checks)


if __name__ == "__main__":
    sys.exit(main())
