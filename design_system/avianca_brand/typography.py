"""
avianca_brand.typography
========================
Tipografía del sistema. Avianca usa **Red Hat Display** en avianca.com, y está
disponible en Google Fonts, así que aquí no hay sustituto: es la fuente real.

Si no está instalada en el sistema, Matplotlib cae a los fallbacks declarados
sin fallar. Para instalarla:

    # macOS
    brew install --cask font-red-hat-display font-red-hat-text
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FontSpec:
    """Especificación de una familia tipográfica con sus reservas."""

    family: str
    fallbacks: List[str] = field(default_factory=list)
    role: str = "body"
    weights: List[int] = field(default_factory=lambda: [400, 500, 700])

    @property
    def stack(self) -> List[str]:
        """La familia seguida de sus fallbacks, tal como la espera Matplotlib."""
        return [self.family] + self.fallbacks

    def __str__(self) -> str:
        return self.family


FONT_DISPLAY = FontSpec(
    family="Red Hat Display",
    fallbacks=["Helvetica Neue", "Arial", "sans-serif"],
    role="display",
    weights=[400, 500, 700, 900],
)
"""Titulares y KPIs. Es la tipografía de avianca.com."""

FONT_TEXT = FontSpec(
    family="Red Hat Text",
    fallbacks=["Red Hat Display", "Helvetica Neue", "Arial", "sans-serif"],
    role="body",
    weights=[400, 500, 700],
)
"""Cuerpo, ejes y etiquetas."""

FONT_MONO = FontSpec(
    family="Red Hat Mono",
    fallbacks=["JetBrains Mono", "Menlo", "Consolas", "monospace"],
    role="mono",
    weights=[400],
)
"""Código, identificadores de modelo y hashes del comprobante."""


@dataclass(frozen=True)
class TypeScale:
    """Escala tipográfica para visualizaciones."""

    figure_title: int = 16
    figure_subtitle: int = 13
    axis_title: int = 12
    data_label: int = 10
    tick_label: int = 10
    legend_title: int = 11
    legend_label: int = 10
    annotation: int = 9
    table_header: int = 11
    table_body: int = 10
    kpi: int = 26


TYPE_SCALE = TypeScale()


def get_matplotlib_font_params(font: FontSpec = FONT_TEXT) -> Dict:
    """
    Parámetros de fuente listos para `matplotlib.rcParams.update()`.

    Examples
    --------
    >>> import matplotlib as mpl
    >>> mpl.rcParams.update(get_matplotlib_font_params())
    """
    scale = TYPE_SCALE
    return {
        "font.family": "sans-serif",
        "font.sans-serif": font.stack,
        "axes.titlesize": scale.figure_title,
        "axes.labelsize": scale.axis_title,
        "xtick.labelsize": scale.tick_label,
        "ytick.labelsize": scale.tick_label,
        "legend.fontsize": scale.legend_label,
        "legend.title_fontsize": scale.legend_title,
        "figure.titlesize": scale.figure_title + 2,
    }
