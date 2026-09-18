"""
avianca_brand.styles
====================
Aplicación global del estilo a Matplotlib y Seaborn.

El tema claro usa papel `#F8F8F8` en vez de blanco puro, y tinta `#1B1B1B` en
vez de negro puro: son los tokens reales de la marca y evitan el contraste duro
que produce un blanco/negro absolutos en pantalla.
"""

from contextlib import contextmanager
from typing import Dict, Literal

import matplotlib as mpl
import matplotlib.pyplot as plt

from avianca_brand.colors import GRIS_CLARO, GRIS_MEDIO, PAPEL, TEXTO, TINTA
from avianca_brand.palettes import CATEGORICAL
from avianca_brand.typography import FONT_TEXT, get_matplotlib_font_params

StyleMode = Literal["light", "dark"]

_BASE = {
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.linewidth": 0.7,
    "grid.alpha": 0.6,
    "axes.axisbelow": True,
    "lines.linewidth": 2.0,
    "lines.markersize": 6,
    "legend.frameon": False,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 14,
    "axes.labelpad": 8,
}


def _light() -> Dict:
    return {
        **_BASE,
        **get_matplotlib_font_params(FONT_TEXT),
        "figure.facecolor": PAPEL.hex,
        "axes.facecolor": PAPEL.hex,
        "savefig.facecolor": PAPEL.hex,
        "text.color": TEXTO.hex,
        "axes.labelcolor": GRIS_MEDIO.hex,
        "axes.edgecolor": GRIS_CLARO.hex,
        "xtick.color": GRIS_MEDIO.hex,
        "ytick.color": GRIS_MEDIO.hex,
        "grid.color": GRIS_CLARO.hex,
        "axes.titlecolor": TINTA.hex,
        "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
    }


def _dark() -> Dict:
    return {
        **_BASE,
        **get_matplotlib_font_params(FONT_TEXT),
        "figure.facecolor": TINTA.hex,
        "axes.facecolor": TINTA.hex,
        "savefig.facecolor": TINTA.hex,
        "text.color": "#F8F8F8",
        "axes.labelcolor": "#B5B5B5",
        "axes.edgecolor": "#3D3D3D",
        "xtick.color": "#B5B5B5",
        "ytick.color": "#B5B5B5",
        "grid.color": "#2E2E2E",
        "axes.titlecolor": "#FFFFFF",
        "axes.prop_cycle": mpl.cycler(color=["#F8F8F8", "#FF0000", "#4FB8C4", "#B5B5B5", "#FF6666", "#7A7A7A"]),
    }


STYLES: Dict[StyleMode, Dict] = {"light": _light(), "dark": _dark()}


def get_style_params(mode: StyleMode = "light") -> Dict:
    """Devuelve el diccionario de rcParams de un tema, sin aplicarlo."""
    if mode not in STYLES:
        raise KeyError(f"Tema '{mode}' no existe. Disponibles: {sorted(STYLES)}")
    return dict(STYLES[mode])


def apply_avianca_style(mode: StyleMode = "light", **overrides) -> None:
    """
    Aplica el estilo globalmente. Llamar una vez al inicio del script.

    Examples
    --------
    >>> import avianca_brand as ab
    >>> ab.apply_avianca_style()
    >>> ab.apply_avianca_style("dark", **{"figure.dpi": 140})
    """
    params = get_style_params(mode)
    params.update(overrides)
    mpl.rcParams.update(params)


def reset_style() -> None:
    """Devuelve Matplotlib a sus valores por defecto."""
    mpl.rcdefaults()


@contextmanager
def avianca_style(mode: StyleMode = "light", **overrides):
    """
    Aplica el estilo solo dentro del bloque.

    Examples
    --------
    >>> with avianca_style("dark"):
    ...     fig, ax = plt.subplots()
    """
    previo = dict(mpl.rcParams)
    try:
        apply_avianca_style(mode, **overrides)
        yield
    finally:
        mpl.rcParams.update(previo)
