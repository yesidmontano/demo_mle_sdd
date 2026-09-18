"""
avianca_brand.palettes
======================
Paletas categóricas, secuenciales y divergentes.

Criterio de orden en las categóricas: **tinta primero, rojo segundo.** La serie
que el lector debe mirar primero es la que lleva el acento de marca, y el resto
se apoya en neutros y en el teal. Una paleta que empieza en rojo obliga a que
todo lo demás compita con él.
"""

from typing import Dict, List

import matplotlib.colors as mcolors

from avianca_brand.colors import (
    ADVERTENCIA,
    GRIS_CLARO,
    GRIS_MEDIO,
    NEGATIVO,
    POSITIVO,
    ROJO,
    ROJO_PROFUNDO,
    ROJO_TEXTO,
    TEAL,
    TINTA,
)

# ─────────────────────────────────────────────
#  CATEGÓRICAS
# ─────────────────────────────────────────────

CATEGORICAL: List[str] = [
    TINTA.hex,
    ROJO.hex,
    TEAL.hex,
    GRIS_MEDIO.hex,
    ROJO_PROFUNDO.hex,
    GRIS_CLARO.hex,
]

CATEGORICAL_EXTENDED: List[str] = CATEGORICAL + [
    "#7A7A7A",
    "#FF6666",
    "#4FB8C4",
    "#3D3D3D",
]

BINARY: List[str] = [TINTA.hex, ROJO.hex]
POSITIVE_NEGATIVE: List[str] = [POSITIVO.hex, NEGATIVO.hex]
TRAFFIC_LIGHT: List[str] = [POSITIVO.hex, ADVERTENCIA.hex, NEGATIVO.hex]


def _sequential(start: str, end: str, name: str) -> mcolors.LinearSegmentedColormap:
    return mcolors.LinearSegmentedColormap.from_list(name, [start, end], N=256)


def _diverging(low: str, mid: str, high: str, name: str) -> mcolors.LinearSegmentedColormap:
    return mcolors.LinearSegmentedColormap.from_list(name, [low, mid, high], N=256)


AVIANCA_REDS = _sequential("#FFF5F5", ROJO_TEXTO.hex, "avianca_reds")
AVIANCA_INKS = _sequential("#F0F0F0", TINTA.hex, "avianca_inks")
AVIANCA_TEALS = _sequential("#E4F5F7", TEAL.hex, "avianca_teals")
AVIANCA_DIVERGING = _diverging(TEAL.hex, "#F8F8F8", ROJO_TEXTO.hex, "avianca_diverging")

_PALETTES: Dict[str, List[str]] = {
    "categorical": CATEGORICAL,
    "categorical_extended": CATEGORICAL_EXTENDED,
    "binary": BINARY,
    "positive_negative": POSITIVE_NEGATIVE,
    "traffic_light": TRAFFIC_LIGHT,
}

_CMAPS: Dict[str, mcolors.LinearSegmentedColormap] = {
    "avianca_reds": AVIANCA_REDS,
    "avianca_inks": AVIANCA_INKS,
    "avianca_teals": AVIANCA_TEALS,
    "avianca_diverging": AVIANCA_DIVERGING,
}


def get_palette(name: str = "categorical") -> List[str]:
    """
    Devuelve una paleta por nombre.

    Raises
    ------
    KeyError
        Si el nombre no existe, con la lista de disponibles.
    """
    if name not in _PALETTES:
        raise KeyError(f"Paleta '{name}' no encontrada. Disponibles: {sorted(_PALETTES)}")
    return list(_PALETTES[name])


def get_cmap(name: str = "avianca_inks") -> mcolors.LinearSegmentedColormap:
    """Devuelve un colormap continuo por nombre."""
    if name not in _CMAPS:
        raise KeyError(f"Colormap '{name}' no encontrado. Disponibles: {sorted(_CMAPS)}")
    return _CMAPS[name]


def make_n_colors(n: int, palette: str = "categorical_extended") -> List[str]:
    """
    Devuelve exactamente `n` colores, interpolando si la paleta se queda corta.

    Examples
    --------
    >>> len(make_n_colors(14))
    14
    """
    base = get_palette(palette)
    if n <= len(base):
        return base[:n]
    cmap = mcolors.LinearSegmentedColormap.from_list("extendida", base, N=max(n, 2))
    return [mcolors.to_hex(cmap(i / (n - 1))) for i in range(n)]


def list_palettes() -> None:
    """Imprime las paletas y colormaps registrados."""
    print("Paletas categóricas:")
    for nombre, colores in _PALETTES.items():
        print(f"  {nombre:22} {len(colores)} colores  {colores[:4]}")
    print("\nColormaps:")
    for nombre in _CMAPS:
        print(f"  {nombre}")
