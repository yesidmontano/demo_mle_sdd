"""Fase 07 — informe de monitoreo: backtest de alertas y resumen del dashboard.

Ejecutar desde la raíz: python code/07_operation_and_monitoring/report.py [--change <id>]
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("gates").resolve()))
import avianca_brand as ab
import _contracts as C
import drift as D
from avianca_brand.colors import GRIS_CLARO, ROJO, TEAL, TINTA

OUT = Path("results/07_operation_and_monitoring")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", default="conversion-sesion-deploy-monitoring")
    change = ap.parse_args().change
    ref = D.load_reference()
    fp = C.load_any(change, "false-positive-budget")[0]
    ab_c = next(c for c in C.load_any(change, "alert-backtest") if "drift_scenario" in c)
    train = pd.read_parquet(fp["reference"])
    no = D.backtest(ref, train, fp["windows"], fp["window_size"], fp["seed"])
    yes = D.backtest(ref, train, ab_c["windows"], ab_c["window_size"], ab_c["seed"], ab_c["drift_scenario"])

    ab.apply_avianca_style()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    bins = np.linspace(0, max(max(no["max_psi"]), max(yes["max_psi"])) * 1.05, 40)
    ax.hist(no["max_psi"], bins=bins, color=GRIS_CLARO.hex, label="Sin desvío")
    ax.hist(yes["max_psi"], bins=bins, color=TINTA.hex, alpha=0.85, label="Con desvío inyectado")
    for x, lab, c in ((D.WARN_PSI, "aviso 0,10", "#B26A00"), (D.ALERT_PSI, "alerta 0,25", ROJO.hex)):
        ax.axvline(x, color=c, lw=1.6)
        ax.text(x + 0.005, ax.get_ylim()[1] * 0.92, lab, color=c, fontsize=10)
    ax.set_xlabel("PSI máximo entre las features, por ventana de 200 inferencias"), ax.set_ylabel("Ventanas")
    ax.legend(loc="upper right")
    ab.style_axes(ax, "Backtest de la regla de alertas",
                  f"Falsos positivos {no['alert_rate']:.1%} · detección con desvío {yes['alert_rate']:.1%} ({fp['windows']} ventanas de cada tipo)")
    (OUT / "imgs").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "imgs/backtest_alertas.png", dpi=150, bbox_inches="tight")

    shot = "![Dashboard](imgs/dashboard.png)\n\n" if (OUT / "imgs/dashboard.png").exists() else ""
    (OUT / "monitoreo.md").write_text(f"""# Monitoreo (simulado en local)

El dashboard es un HTML autocontenido, sin red y con la marca aplicada: [dashboard.html](dashboard.html). Un HTML
abierto desde `file://` no puede leer Parquet, así que la «conexión» con Gold es un paso de construcción que lee
`data/gold/inferences/` y calcula las señales con la misma lógica que los gates de alertas (`drift.py`):

```bash
python code/07_operation_and_monitoring/build_dashboard.py
```

{shot}## Señales

| Señal | Ventana | Aviso | Alerta | Acción |
|---|---|---|---|---|
| PSI de feature o de puntuación | 200 inferencias | ≥ 0,10 | ≥ 0,25 | investigar el origen; si persiste, change de reentrenamiento |
| Latencia p99 por sesión | 200 | > 250 ms | > 500 ms | revisar carga y tamaño del modelo |
| Tasa de rechazo | 200 | > 1 % | > 5 % | revisar el contrato de entrada |
| Categorías no vistas | 200 | > 5 % | > 15 % | reentrenar con las nuevas categorías |
| Tasa de intervención vs K | 200 | ±5 pp | ±10 pp | revisar umbral y puntuaciones |

Con menos de 200 inferencias el estado es «datos insuficientes», no verde. Además: volumen, versión servida,
segmentos (canal, tipo de viaje, tramo de antelación) y las últimas inferencias.

## ¿Las alertas son confiables? Backtest

![Backtest de alertas](imgs/backtest_alertas.png)

Sobre ventanas de 200 filas de `train`: **{no['alert_rate']:.1%}** de falsas alertas sin desvío (presupuesto 5 %) y
**{yes['alert_rate']:.1%}** de detección cuando se sobremuestrea `sales_channel = Mobile` cinco veces (mínimo 90 %).
El PSI máximo mediano sin desvío es {no['median_max_psi']:.3f}, por debajo del aviso: el ruido de muestreo no toca los umbrales.

## Límites

- El dashboard es una vista estática: se refresca reconstruyéndolo.
- El tráfico de la demo es simulado (`source = simulation`); el desvío de la ventana final se inyectó a propósito.
- No hay resultados de conversión en línea: no se monitorea el desempeño del modelo, solo entradas, salidas y operación.
""")
    print(f"backtest: FP={no['alert_rate']:.3f} detección={yes['alert_rate']:.3f}")


if __name__ == "__main__":
    main()
