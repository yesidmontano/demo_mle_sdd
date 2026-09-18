"""Simula tráfico para el monitoreo: muchos lotes pequeños con la MISMA función de despliegue.

Las filas quedan marcadas `source = simulation`, con horas repartidas hacia atrás en el tiempo, y con
`--drift-from-batch N` los lotes desde N sobremuestrean `sales_channel = Mobile` (desvío inyectado).

  python code/06-deploy/simulate_traffic.py --batches 120 --drift-from-batch 80 --reset
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
import common
import predict as P


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--model-version")
    g.add_argument("--model-alias")
    ap.add_argument("--batches", type=int, default=120)
    ap.add_argument("--minutes-between", type=int, default=45, help="separación entre lotes simulados")
    ap.add_argument("--drift-from-batch", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--source", type=Path, default=P.BRONZE)
    ap.add_argument("--out", type=Path, default=P.OUT_DIR)
    ap.add_argument("--reset", action="store_true", help="borra las inferencias `simulation` previas de --out")
    a = ap.parse_args()

    common.init_mlflow()
    info = P.resolve(common.REGISTERED_MODEL, a.model_version, a.model_alias)
    model, load_ms = P.load(info)
    df, rng = P.read_source(a.source), np.random.default_rng(a.seed)
    if a.reset and a.out.exists():
        import pandas as pd
        for f in a.out.glob("inferences_*.parquet"):
            if (pd.read_parquet(f, columns=["source"])["source"] == "simulation").all():
                f.unlink()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    rows_total = 0
    for i in range(a.batches):
        drifted = a.drift_from_batch is not None and i >= a.drift_from_batch
        n = int(rng.integers(2, 4))
        rows = P.sample_rows(df, n, int(rng.integers(0, 2**31)), ("sales_channel", "Mobile", 5) if drifted else None)
        ts = now - timedelta(minutes=a.minutes_between * (a.batches - 1 - i))
        P.run_inference(rows, info, model=model, model_load_ms=load_ms if i == 0 else None, out_dir=a.out,
                        source="simulation", timestamp=ts, seed=a.seed)
        rows_total += n
    print(f"{a.batches} lotes, {rows_total} inferencias simuladas con v{info['version']} en {a.out}/"
          + (f" (desvío desde el lote {a.drift_from_batch})" if a.drift_from_batch is not None else ""))


if __name__ == "__main__":
    main()
