"""
avianca_brand.layout
====================
Figuras multi-panel y tarjetas de KPI con la cabecera del sistema.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import matplotlib.pyplot as plt

from avianca_brand.colors import GRIS_CLARO, GRIS_MEDIO, ROJO, TINTA
from avianca_brand.typography import TYPE_SCALE


@dataclass(frozen=True)
class FigureSizes:
    """Tamaños canónicos, en pulgadas."""

    single: Tuple[float, float] = (10, 5.5)
    wide: Tuple[float, float] = (14, 5.5)
    square: Tuple[float, float] = (8, 8)
    dashboard: Tuple[float, float] = (16, 10)
    slide: Tuple[float, float] = (13.33, 7.5)
    kpi: Tuple[float, float] = (12, 3)


SIZES = FigureSizes()

_TITLE_Y = 0.975
_SUBTITLE_Y = 0.935
_RULE_Y = 0.912


def _header(fig: plt.Figure, title: str, subtitle: str = "") -> None:
    """Título, subtítulo y la regla roja que los separa del contenido."""
    if title:
        fig.text(0.02, _TITLE_Y, title, fontsize=TYPE_SCALE.figure_title + 4,
                 fontweight="bold", color=TINTA.hex, ha="left", va="top")
    if subtitle:
        fig.text(0.02, _SUBTITLE_Y, subtitle, fontsize=TYPE_SCALE.figure_subtitle,
                 color=GRIS_MEDIO.hex, ha="left", va="top")
    if title:
        fig.add_artist(plt.Line2D([0.02, 0.10], [_RULE_Y, _RULE_Y],
                                  color=ROJO.hex, linewidth=3, transform=fig.transFigure))


def create_dashboard(nrows: int, ncols: int, title: str = "", subtitle: str = "",
                     figsize: Optional[Tuple[float, float]] = None, **kwargs):
    """
    Rejilla de paneles con cabecera de marca.

    Returns
    -------
    (Figure, ndarray[Axes])
    """
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize or SIZES.dashboard, **kwargs)
    _header(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0.02, 1, 0.88 if title else 1.0))
    return fig, axes


def create_report_figure(title: str = "", subtitle: str = "",
                         figsize: Optional[Tuple[float, float]] = None):
    """Figura de un solo panel con cabecera, para incrustar en un reporte."""
    fig, ax = plt.subplots(figsize=figsize or SIZES.single)
    _header(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0.02, 1, 0.86 if title else 1.0))
    return fig, ax


def create_kpi_figure(kpis: Sequence[Tuple[str, str, Optional[str]]], title: str = "",
                      subtitle: str = "", figsize: Optional[Tuple[float, float]] = None):
    """
    Fila de KPIs. Cada uno es `(etiqueta, valor, delta)`; `delta` puede ser None.

    El delta lleva su signo en el texto además del color: un lector que no
    distingue rojo de verde debe poder leerlo igual.
    """
    fig, axes = plt.subplots(1, len(kpis), figsize=figsize or SIZES.kpi)
    axes = [axes] if len(kpis) == 1 else list(axes)
    _header(fig, title, subtitle)

    for ax, (etiqueta, valor, delta) in zip(axes, kpis):
        ax.axis("off")
        ax.text(0.5, 0.72, valor, fontsize=TYPE_SCALE.kpi, fontweight="bold",
                color=TINTA.hex, ha="center", va="center")
        ax.text(0.5, 0.34, etiqueta, fontsize=TYPE_SCALE.legend_label,
                color=GRIS_MEDIO.hex, ha="center", va="center")
        if delta:
            negativo = delta.strip().startswith("-")
            ax.text(0.5, 0.10, delta, fontsize=TYPE_SCALE.annotation,
                    color=ROJO.hex if negativo else "#1EA93C", ha="center", va="center")
        for lado in ("left", "right"):
            ax.spines[lado].set_visible(False)
    fig.tight_layout(rect=(0, 0.02, 1, 0.84 if title else 1.0))
    return fig, axes
