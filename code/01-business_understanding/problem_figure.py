"""Fase 01 — diagrama del embudo de decisión. Ejecutar desde la raíz del repo."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import avianca_brand as ab
from avianca_brand.colors import GRIS_CLARO, ROJO, TINTA

OUT = Path("results/01-business_understanding/imgs/embudo_decision.png")


def main() -> None:
    ab.apply_avianca_style()
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 104), ax.set_ylim(0, 40), ax.axis("off")
    pasos = [
        ("Sesiones de\nreserva", "todas las sesiones", GRIS_CLARO.hex, TINTA.hex),
        ("Modelo de\nprobabilidad", "P(booking_complete)\nordena las sesiones", TINTA.hex, "white"),
        ("Umbral / top-K", "fijado en la spec\nde evaluation", ROJO.hex, "white"),
        ("Intervención", "recordatorio, descuento,\nretargeting (presupuesto fijo)", GRIS_CLARO.hex, TINTA.hex),
        ("Ingreso\nincremental", "fracción convertida\n× ticket medio (supuesto)", TINTA.hex, "white"),
    ]
    w, gap = 17, 3.75
    for i, (t, sub, fc, tc) in enumerate(pasos):
        x = 1 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 16), w, 14, boxstyle="round,pad=0.4", fc=fc, ec="none"))
        ax.text(x + w / 2, 23, t, ha="center", va="center", color=tc, fontsize=11, fontweight="bold")
        ax.text(x + w / 2, 11, sub, ha="center", va="top", color=TINTA.hex, fontsize=9)
        if i < len(pasos) - 1:
            ax.annotate("", xy=(x + w + gap - 0.3, 23), xytext=(x + w + 0.5, 23),
                        arrowprops=dict(arrowstyle="->", color=TINTA.hex, lw=1.6))
    ax.set_title("Del ranking al ingreso: el modelo ordena, el umbral decide", loc="left",
                 fontsize=15, fontweight="bold", color=TINTA.hex)
    ax.text(0, 2, "El eslabón «fracción convertida × ticket medio» es un supuesto, no una medición.",
            fontsize=9, color="#5A5A5A")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(OUT)


if __name__ == "__main__":
    main()
