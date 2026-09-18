"""
avianca_brand
=============
Sistema de diseño de Avianca para visualización de datos.

Implementa los design tokens publicados en avianca.com —colores, tipografía,
paletas, estilos y componentes— para que toda figura del proyecto salga con la
misma identidad sin decidirlo caso por caso.

Módulos
-------
colors      : Primarios, secundarios, neutros y semánticos, con su token origen.
typography  : Red Hat Display / Text / Mono y la escala tipográfica.
palettes    : Paletas categóricas, secuenciales y divergentes.
styles      : Aplicación global del tema a Matplotlib.
charts      : Gráficas de alto nivel con la marca puesta.
layout      : Dashboards, figuras de reporte y filas de KPI.

Uso rápido
----------
    >>> import avianca_brand as ab

    >>> ab.apply_avianca_style()            # tema claro (por defecto)
    >>> ab.apply_avianca_style("dark")      # tema oscuro

    >>> ab.colors.ROJO.hex                  # '#FF0000'
    >>> ab.get_palette("categorical")

    >>> fig, ax = ab.bar_chart(x, y, title="Ingreso por ruta", highlight=0)
    >>> fig, ax = ab.slice_chart(slices, base, cand, title="MAE por segmento")

Lo que conviene saber antes de usarlo
-------------------------------------
**El primario de Avianca es la tinta `#1B1B1B`, no el rojo.** Su propio token
`--logo-avianca-primary` resuelve a ese casi-negro. El rojo `#FF0000` es acento:
sirve para la serie principal, para destacar *una* categoría y para marcar lo
que empeora. Usado como color dominante, contradice la marca y además pierde
legibilidad — sobre blanco da ~4:1, así que para texto pequeño está
`ROJO_TEXTO` (`#CC0000`, ~5.3:1).

Referencia de color
-------------------
    Tinta          #1B1B1B   --brand-primary        Primario
    Rojo           #FF0000   --red-500              Acento de marca
    Rojo Texto     #CC0000   --red-600              Acento accesible
    Rojo Profundo  #990000   --red-700              Secundario
    Teal           #0190A0   --link-color-secondary Contraste frío
    Texto          #131313   --text-color           Neutro
    Gris Medio     #5A5A5A   --text-brand-disable   Neutro
    Gris Claro     #D9D9D9   --state-disabled       Neutro
    Papel          #F8F8F8   --light-color          Fondo
"""

__version__ = "0.1.0"

from avianca_brand import charts, colors, layout, palettes, styles, typography
from avianca_brand.charts import (
    add_footer,
    add_logo,
    bar_chart,
    correlation_heatmap,
    dist_chart,
    line_chart,
    scatter_chart,
    slice_chart,
    style_axes,
)
from avianca_brand.colors import (
    BLANCO,
    GRIS_CLARO,
    GRIS_MEDIO,
    PAPEL,
    ROJO,
    ROJO_PROFUNDO,
    ROJO_TEXTO,
    TEAL,
    TEXTO,
    TINTA,
    get_color,
    list_colors,
)
from avianca_brand.layout import SIZES, create_dashboard, create_kpi_figure, create_report_figure
from avianca_brand.palettes import get_cmap, get_palette, list_palettes, make_n_colors
from avianca_brand.styles import apply_avianca_style, avianca_style, reset_style

__all__ = [
    "charts", "colors", "layout", "palettes", "styles", "typography",
    "apply_avianca_style", "avianca_style", "reset_style",
    "TINTA", "ROJO", "ROJO_TEXTO", "ROJO_PROFUNDO", "TEAL",
    "TEXTO", "GRIS_MEDIO", "GRIS_CLARO", "PAPEL", "BLANCO",
    "get_color", "list_colors",
    "get_palette", "get_cmap", "make_n_colors", "list_palettes",
    "add_logo", "add_footer", "style_axes",
    "bar_chart", "line_chart", "dist_chart", "scatter_chart",
    "correlation_heatmap", "slice_chart",
    "create_dashboard", "create_report_figure", "create_kpi_figure", "SIZES",
]
