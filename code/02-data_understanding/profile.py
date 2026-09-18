"""Fase 02 — perfil de bronze y verificación de fuga de `wants_*`.

Ejecutar desde la raíz del repo: python code/02-data_understanding/profile.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import avianca_brand as ab
from avianca_brand.colors import GRIS_CLARO, ROJO, TINTA

BRONZE = Path("data/bronze/customer_booking.csv")
OUT = Path("results/02-data_understanding")
IMGS = OUT / "imgs"
WANTS = ["wants_extra_baggage", "wants_preferred_seat", "wants_in_flight_meals"]
NUMS = ["num_passengers", "purchase_lead", "length_of_stay", "flight_hour", "flight_duration"]


def save(fig, name: str) -> str:
    IMGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMGS / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return f"imgs/{name}"


def main() -> None:
    ab.apply_avianca_style()
    df = pd.read_csv(BRONZE, encoding="latin1")
    y = df["booking_complete"]
    rate = y.mean()
    dups = int(df.duplicated().sum())

    # Figura 1 — balance de clases
    fig, ax = ab.bar_chart(["No completa", "Completa"], [(1 - rate) * 100, rate * 100], highlight=1,
                           title="La clase positiva es minoritaria", subtitle=f"{rate:.1%} de {len(df):,} sesiones completan la reserva",
                           ylabel="% de sesiones")
    f_balance = save(fig, "balance_clases.png")

    # Figura 2 — distribuciones numéricas
    fig, axes = ab.create_dashboard(2, 3, title="Rangos y distribuciones de las variables numéricas",
                                    subtitle="Colas largas en purchase_lead y length_of_stay", figsize=(13, 8))
    for ax, c in zip(axes.flat, NUMS):
        ax.hist(df[c], bins=30, color=TINTA.hex, alpha=0.85)
        ax.set_title(f"{c}  (min {df[c].min():g} · max {df[c].max():g})", fontsize=10)
    axes.flat[-1].axis("off")
    f_dist = save(fig, "distribuciones_numericas.png")

    # Figura 3 — wants_* por clase (verificación de fuga)
    tab = df.groupby("booking_complete")[WANTS].mean().T * 100
    fig, ax = plt.subplots(figsize=(9, 5))
    xs = np.arange(len(WANTS))
    ax.bar(xs - 0.2, tab[0], 0.4, color=GRIS_CLARO.hex, label="No completa")
    ax.bar(xs + 0.2, tab[1], 0.4, color=ROJO.hex, label="Completa")
    ax.set_xticks(xs, [w.replace("wants_", "") for w in WANTS])
    ax.set_ylabel("% con la bandera = 1"), ax.legend()
    ab.style_axes(ax, "Las banderas no son todo ceros en sesiones no completadas",
                  "Si solo se rellenaran al completar, la barra gris sería 0")
    f_wants = save(fig, "wants_por_clase.png")

    # Figura 4 — conversión por segmento
    df["lead_bucket"] = pd.cut(df["purchase_lead"], [-1, 7, 30, 90, 180, 10_000],
                               labels=["0-7", "8-30", "31-90", "91-180", ">180"])
    fig, axes = ab.create_dashboard(1, 3, title="Conversión por segmento",
                                    subtitle=f"La línea roja marca la media global: {rate:.1%}",
                                    figsize=(14, 5.6), sharey=True)
    for ax, c in zip(axes, ["sales_channel", "trip_type", "lead_bucket"]):
        g = df.groupby(c, observed=True)["booking_complete"].mean() * 100
        ax.bar(g.index.astype(str), g.values, color=TINTA.hex)
        ax.axhline(rate * 100, color=ROJO.hex, ls="--", lw=1.4)
        ax.set_title(c, loc="left", fontsize=11)
    axes[0].set_ylabel("% conversión")
    f_slice = save(fig, "conversion_por_segmento.png")

    # Veredicto de fuga
    zero_nc = {w: float(tab.loc[w, 0]) for w in WANTS}
    leak = all(v == 0 for v in zero_nc.values())
    veredicto = ("**FUGA**: las banderas valen 0 en toda sesión no completada; descartarlas."
                 if leak else
                 "**Sin fuga por construcción**: las sesiones no completadas tienen banderas en 1, así que se "
                 "seleccionan durante la sesión. Se conservan como features.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "profile.md").write_text(f"""# Perfil de bronze — `customer_booking.csv`

| | |
|---|---|
| Filas · columnas | {len(df):,} · {df.shape[1]} |
| Nulos | {int(df.isna().sum().sum())} |
| Filas duplicadas exactas | {dups} ({dups / len(df):.2%}) |
| Tasa de positivos | {rate:.2%} |
| Cardinalidad `route` · `booking_origin` | {df.route.nunique()} · {df.booking_origin.nunique()} |

![Balance de clases]({f_balance})

La clase positiva es minoritaria: métricas como *accuracy* engañan; hay que calibrar y evaluar por segmento.

![Distribuciones]({f_dist})

Hay colas largas en `purchase_lead` y `length_of_stay`; los rangos del contrato de datos se fijan con estos máximos.

![Conversión por segmento]({f_slice})

La conversión cambia con canal, tipo de viaje y antelación: hay segmentos con qué trabajar en `slice-eval`.

## Decisiones

- **Duplicados**: no hay id de sesión, así que las {dups} filas idénticas se eliminan en silver (ver fase 03).
- **Fuga de `wants_*`**: ver [wants_leakage.md](wants_leakage.md).
""")
    (OUT / "wants_leakage.md").write_text(f"""# ¿Filtran las banderas `wants_*` el objetivo?

Pregunta: ¿qué significa `wants_* = 0` en una sesión no completada?

![wants por clase]({f_wants})

| Bandera | % en 1, no completa | % en 1, completa |
|---|---|---|
""" + "\n".join(f"| {w} | {tab.loc[w, 0]:.1f} % | {tab.loc[w, 1]:.1f} % |" for w in WANTS) + f"""

## Veredicto

{veredicto}

**Supuesto**: la semántica se infiere de los datos, no de una definición del sistema fuente; reconfirmar con la
persona dueña del dato antes de servir. Esta decisión alimenta `conversion-sesion-features`.
""")
    print("perfil ok", {"rows": len(df), "dups": dups, "rate": round(rate, 4), "leak": leak})


if __name__ == "__main__":
    main()
