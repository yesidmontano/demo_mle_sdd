"""Fase 06 — informe de despliegue: latencia por sesión y registro de versiones.

Ejecutar desde la raíz: python code/06-deploy/report.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mlflow import MlflowClient

sys.path.insert(0, str(Path("gates").resolve()))
for d in ("code/05-evaluation", "code/06-deploy"):
    sys.path.insert(0, str(Path(d).resolve()))
import avianca_brand as ab
import common
import latency_p99 as L
import predict as P
from avianca_brand.colors import GRIS_CLARO, ROJO, TEAL, TINTA

OUT = Path("results/06-deploy")


def main() -> None:
    common.init_mlflow()
    client = MlflowClient()
    mvs = sorted(client.search_model_versions(f"name='{common.REGISTERED_MODEL}'"), key=lambda m: int(m.version))
    champion = next((m.version for m in mvs if "champion" in (m.aliases or [])), None)
    cand = str(max(int(m.version) for m in mvs if m.tags.get("role") == "candidate"))
    info = P.resolve(common.REGISTERED_MODEL, cand, None)
    model, load_ms = P.load(info)
    lat = np.array(L.measure(model, info, 200))
    p50, p99 = np.percentile(lat, [50, 99])

    ab.apply_avianca_style()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.hist(lat, bins=30, color=TINTA.hex, alpha=0.85)
    ax.axvline(p50, color=TEAL.hex, lw=2), ax.axvline(p99, color=ROJO.hex, lw=2), ax.axvline(250, color=GRIS_CLARO.hex, lw=2)
    top = ax.get_ylim()[1]
    for x, lab, c in ((p50, f"p50 {p50:.0f} ms", TEAL.hex), (p99, f"p99 {p99:.0f} ms", ROJO.hex), (250, "umbral 250 ms", "#5A5A5A")):
        ax.text(x - 3 if x >= 250 else x + 3, top * 0.93, lab, color=c, fontsize=10, ha="right" if x >= 250 else "left")
    ax.set_xlabel("Latencia por sesión (ms), una fila por llamada"), ax.set_ylabel("Inferencias")
    ab.style_axes(ax, "Latencia de la función de despliegue", f"200 sesiones, modelo precalentado; p99 = {p99:.0f} ms frente a un presupuesto de 250 ms")
    (OUT / "imgs").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "imgs/latencia_sesion.png", dpi=150, bbox_inches="tight")

    rows = "\n".join(f"| v{m.version} | {m.tags.get('role')} | `{m.tags.get('run_id', '')[:12]}` | {m.tags.get('decision_threshold')} | "
                     f"{', '.join(m.aliases) or '—'} |" for m in mvs)
    (OUT / "despliegue.md").write_text(f"""# Despliegue (simulado en local)

No hay nube: el «despliegue» es una función con comando de ejecución que sirve sesiones con una versión del
modelo registrado y guarda cada inferencia en `data/gold/inferences/`.

## Modelo registrado (`{common.REGISTERED_MODEL}`)

| Versión | Rol | Run de MLflow | Umbral de decisión | Alias |
|---|---|---|---|---|
{rows}

La v1 (línea base) es el destino de rollback; la v2 (candidato sellado) solo recibe `champion` con comprobante
(`openspec/changes/.../evidence/receipt.json`). El umbral de decisión es el cuantil `1 - K` de las puntuaciones de
test (K = 20 %, de la spec de evaluation).

## Comandos

```bash
# 3 sesiones al azar con el alias champion
python code/06-deploy/predict.py

# otra versión del modelo registrado, o un lote reproducible
python code/06-deploy/predict.py --model-version 1
python code/06-deploy/predict.py --n-rows 2 --seed 7

# tráfico simulado para el monitoreo (marca source = simulation), con desvío desde el lote 220
python code/06-deploy/simulate_traffic.py --model-version 2 --batches 300 --drift-from-batch 220 --reset

# rollback: reapuntar champion a la versión anterior
python code/06-deploy/promote.py --version 1
```

Cada inferencia guarda: `inference_id`, `batch_id`, `timestamp_utc`, `source`, `model_name`, `model_version`,
`model_alias`, `model_run_id`, `prob_conversion`, `intervene`, `decision_threshold`, `latency_ms` (por sesión),
`model_load_ms`, `status`, `reject_reason` y **las entradas** con prefijo `in_`, base del data drift. Una fila con
datos ausentes o inválidos se registra `rejected` sin detener el lote.

## Latencia

![Latencia por sesión](imgs/latencia_sesion.png)

Con el modelo precalentado, la mediana es {p50:.0f} ms y el p99 {p99:.0f} ms por llamada completa (validación,
pipeline y predicción), por debajo del presupuesto de 250 ms. La carga inicial del modelo tarda {load_ms / 1000:.1f} s y
se registra aparte (`model_load_ms`). Es latencia local, no un compromiso de producción.

## Límites

- `mlflow.db` y `mlartifacts/` no se versionan: un clon limpio debe reejecutar la fase 04 y `register_model.py`.
- Sin resultados reales de conversión en línea no se puede medir el desempeño del modelo servido.
""")
    print(f"p50={p50:.1f} ms p99={p99:.1f} ms · versiones={[m.version for m in mvs]} · champion={champion}")


if __name__ == "__main__":
    main()
