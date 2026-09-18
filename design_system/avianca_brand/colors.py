"""
avianca_brand.colors
====================
Paleta oficial de Avianca, extraída de los design tokens publicados en
avianca.com (`--brand-primary`, la escala `--red-*`, neutros y semánticos).

Hallazgo que condiciona todo el sistema: **el primario de Avianca es el
casi-negro `#1B1B1B`, no el rojo.** Su propio token `--logo-avianca-primary`
resuelve a `#1B1B1B`. El rojo es acento y se reserva para la serie principal,
el énfasis y las alertas; usarlo como color dominante contradice la marca.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Color:
    """Un color de marca con sus distintas representaciones."""

    name: str
    hex: str
    rgb: Tuple[int, int, int]
    token: str = ""
    role: str = ""

    @property
    def rgb_normalized(self) -> Tuple[float, float, float]:
        """RGB en el rango [0, 1], que es lo que consume Matplotlib."""
        return tuple(c / 255.0 for c in self.rgb)

    def with_alpha(self, alpha: float) -> Tuple[float, float, float, float]:
        """El color con la transparencia indicada."""
        r, g, b = self.rgb_normalized
        return (r, g, b, alpha)

    def __str__(self) -> str:
        return self.hex


# ─────────────────────────────────────────────
#  PRIMARIOS
# ─────────────────────────────────────────────

TINTA = Color(
    name="Tinta Avianca",
    hex="#1B1B1B",
    rgb=(27, 27, 27),
    token="--brand-primary",
    role="primary",
)
"""Primario real de la marca. Texto, fondos oscuros y el logo sobre claro."""

ROJO = Color(
    name="Rojo Avianca",
    hex="#FF0000",
    rgb=(255, 0, 0),
    token="--red-500",
    role="primary",
)
"""Acento de marca. Solo a tamaño display o como serie principal: sobre blanco
da ~4:1, insuficiente para texto pequeño. Para eso está ROJO_TEXTO."""

# ─────────────────────────────────────────────
#  SECUNDARIOS
# ─────────────────────────────────────────────

ROJO_TEXTO = Color(
    name="Rojo Texto",
    hex="#CC0000",
    rgb=(204, 0, 0),
    token="--red-600",
    role="secondary",
)
"""Variante accesible del rojo: ~5.3:1 sobre #F8F8F8. Úsalo en texto y ejes."""

ROJO_PROFUNDO = Color(
    name="Rojo Profundo",
    hex="#990000",
    rgb=(153, 0, 0),
    token="--red-700",
    role="secondary",
)

TEAL = Color(
    name="Teal Avianca",
    hex="#0190A0",
    rgb=(1, 144, 160),
    token="--link-color-secondary",
    role="secondary",
)
"""Acento frío. Segunda serie, y el contraste natural del rojo sin competir."""

# ─────────────────────────────────────────────
#  NEUTROS
# ─────────────────────────────────────────────

TEXTO = Color(name="Texto", hex="#131313", rgb=(19, 19, 19), token="--text-color", role="neutral")
GRIS_MEDIO = Color(name="Gris Medio", hex="#5A5A5A", rgb=(90, 90, 90), token="--text-brand-disable", role="neutral")
GRIS_CLARO = Color(name="Gris Claro", hex="#D9D9D9", rgb=(217, 217, 217), token="--state-disabled", role="neutral")
PAPEL = Color(name="Papel", hex="#F8F8F8", rgb=(248, 248, 248), token="--light-color", role="neutral")
BLANCO = Color(name="Blanco", hex="#FFFFFF", rgb=(255, 255, 255), role="neutral")

# ─────────────────────────────────────────────
#  SEMÁNTICOS
# ─────────────────────────────────────────────

POSITIVO = Color(name="Positivo", hex="#1EA93C", rgb=(30, 169, 60), token="--green-primary", role="semantic")
NEGATIVO = Color(name="Negativo", hex="#CC0000", rgb=(204, 0, 0), token="--red-600", role="semantic")
ADVERTENCIA = Color(name="Advertencia", hex="#B26A00", rgb=(178, 106, 0), role="semantic")
INFORMACION = Color(name="Información", hex="#1D9BF0", rgb=(29, 155, 240), token="--focus-primary", role="semantic")

# ─────────────────────────────────────────────
#  COLECCIONES
# ─────────────────────────────────────────────

PRIMARY: Dict[str, Color] = {"tinta": TINTA, "rojo": ROJO}
SECONDARY: Dict[str, Color] = {"rojo_texto": ROJO_TEXTO, "rojo_profundo": ROJO_PROFUNDO, "teal": TEAL}
NEUTRAL: Dict[str, Color] = {"texto": TEXTO, "gris_medio": GRIS_MEDIO, "gris_claro": GRIS_CLARO, "papel": PAPEL, "blanco": BLANCO}
SEMANTIC: Dict[str, Color] = {"positivo": POSITIVO, "negativo": NEGATIVO, "advertencia": ADVERTENCIA, "informacion": INFORMACION}

ALL_COLORS: Dict[str, Color] = {**PRIMARY, **SECONDARY, **NEUTRAL, **SEMANTIC}


def get_color(name: str) -> Color:
    """
    Recupera un color por su nombre clave.

    Raises
    ------
    KeyError
        Si el nombre no existe, con la lista de disponibles.

    Examples
    --------
    >>> get_color("rojo").hex
    '#FF0000'
    """
    if name not in ALL_COLORS:
        raise KeyError(f"Color '{name}' no encontrado. Disponibles: {sorted(ALL_COLORS)}")
    return ALL_COLORS[name]


def list_colors() -> None:
    """Imprime el catálogo completo agrupado por rol."""
    for grupo, coleccion in [
        ("Primarios", PRIMARY),
        ("Secundarios", SECONDARY),
        ("Neutros", NEUTRAL),
        ("Semánticos", SEMANTIC),
    ]:
        print(f"\n{'=' * 46}\n  {grupo}\n{'=' * 46}")
        for clave, color in coleccion.items():
            token = f"  [{color.token}]" if color.token else ""
            print(f"  [{clave}]  {color.name}{token}")
            print(f"    HEX: {color.hex}  |  RGB: {color.rgb}")
