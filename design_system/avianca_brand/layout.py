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

# La cabecera se mide en PULGADAS, no en fracción de la figura: una fracción fija
# ocupa lo mismo en una figura de 4,6 in que en una de 10 in, y en la baja se
# come el área de los paneles y los títulos se pisan.
_MARGIN_IN = 0.15      # aire sobre el título
_TITLE_IN = 0.36       # alto de la línea de título
_SUBTITLE_IN = 0.28    # alto de la línea de subtítulo
_RULE_IN = 0.18        # regla roja + aire antes del contenido


def _header(fig: plt.Figure, title: str, subtitle: str = "") -> float:
    """
    Título, subtítulo y la regla roja que los separa del contenido.

    Devuelve el borde superior (0-1) que deben respetar los paneles, para pasarlo
    a `tight_layout(rect=...)`.
    """
    if not title:
        return 1.0
    h = fig.get_figheight()
    y = 1 - _MARGIN_IN / h
    fig.text(0.02, y, title, fontsize=TYPE_SCALE.figure_title + 4,
             fontweight="bold", color=TINTA.hex, ha="left", va="top")
    y -= _TITLE_IN / h
    if subtitle:
        fig.text(0.02, y, subtitle, fontsize=TYPE_SCALE.figure_subtitle,
                 color=GRIS_MEDIO.hex, ha="left", va="top")
        y -= _SUBTITLE_IN / h
    y -= 0.04 / h
    fig.add_artist(plt.Line2D([0.02, 0.10], [y, y], color=ROJO.hex, linewidth=3,
                              transform=fig.transFigure))
    return y - _RULE_IN / h


def create_dashboard(nrows: int, ncols: int, title: str = "", subtitle: str = "",
                     figsize: Optional[Tuple[float, float]] = None, **kwargs):
    """
    Rejilla de paneles con cabecera de marca.

    Returns
    -------
    (Figure, ndarray[Axes])
    """
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize or SIZES.dashboard, **kwargs)
    top = _header(fig, title, subtitle)
    # h_pad/w_pad generosos: sin ellos las etiquetas del eje x de una fila tocan
    # el título del panel de la fila siguiente.
    fig.tight_layout(rect=(0, 0.02, 1, top), h_pad=2.5, w_pad=2.0)
    return fig, axes


def create_report_figure(title: str = "", subtitle: str = "",
                         figsize: Optional[Tuple[float, float]] = None):
    """Figura de un solo panel con cabecera, para incrustar en un reporte."""
    fig, ax = plt.subplots(figsize=figsize or SIZES.single)
    top = _header(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0.02, 1, top))
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
    top = _header(fig, title, subtitle)

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
    fig.tight_layout(rect=(0, 0.02, 1, top))
    return fig, axes
