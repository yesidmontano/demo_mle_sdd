"""
avianca_brand.charts
====================
Gráficas de alto nivel con la marca aplicada.

Todas devuelven `(fig, ax)` para que el llamante conserve el control: estas
funciones ponen el estilo, no deciden por ti qué gráfico necesitas.
"""

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

from avianca_brand.colors import GRIS_CLARO, GRIS_MEDIO, ROJO, TEAL, TINTA
from avianca_brand.palettes import get_cmap, get_palette, make_n_colors
from avianca_brand.typography import TYPE_SCALE

_ASSETS = Path(__file__).parent / "assets"
_LOGO_SVG = _ASSETS / "logo.svg"
_LOGO_PNG = _ASSETS / "logo.png"


def add_logo(ax: plt.Axes, loc: str = "upper right", zoom: float = 0.10, alpha: float = 0.9) -> None:
    """
    Coloca el logo sobre los ejes, si hay un PNG disponible.

    El logo de referencia es `assets/logo.svg`. Matplotlib no rasteriza SVG, así
    que esta función solo actúa cuando existe `assets/logo.png`; si no, no hace
    nada y **no falla**, para que una figura nunca se pierda por un asset.
    """
    if not _LOGO_PNG.exists():
        return
    from matplotlib.offsetbox import AnnotationBbox, OffsetImage

    img = plt.imread(_LOGO_PNG)
    xy = {"upper right": (0.98, 0.98), "upper left": (0.02, 0.98),
          "lower right": (0.98, 0.04), "lower left": (0.02, 0.04)}.get(loc, (0.98, 0.98))
    box = OffsetImage(img, zoom=zoom, alpha=alpha)
    ax.add_artist(AnnotationBbox(box, xy, xycoords="axes fraction", frameon=False,
                                 box_alignment=(1 if "right" in loc else 0, 1 if "upper" in loc else 0)))


def add_footer(fig: plt.Figure, texto: str, fuente: Optional[str] = None) -> None:
    """Añade una línea de pie con la procedencia del dato."""
    completo = texto if fuente is None else f"{texto}  ·  Fuente: {fuente}"
    fig.text(0.01, 0.01, completo, fontsize=TYPE_SCALE.annotation,
             color=GRIS_MEDIO.hex, ha="left", va="bottom")


def style_axes(ax: plt.Axes, title: str = "", subtitle: str = "",
               xlabel: str = "", ylabel: str = "") -> plt.Axes:
    """
    Aplica títulos con la jerarquía del sistema.

    El subtítulo va en gris y un cuerpo por debajo del título: separar el qué
    del contexto es lo que evita titulares de dos renglones.
    """
    if title:
        ax.set_title(title, fontsize=TYPE_SCALE.figure_title, color=TINTA.hex,
                     fontweight="bold", loc="left", pad=26 if subtitle else 14)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=TYPE_SCALE.figure_subtitle,
                color=GRIS_MEDIO.hex, ha="left", va="bottom")
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    return ax


def bar_chart(x: Sequence, y: Sequence, title: str = "", subtitle: str = "",
              xlabel: str = "", ylabel: str = "", highlight: Optional[int] = None,
              horizontal: bool = False, figsize: Tuple[float, float] = (10, 5.5),
              ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Barras. `highlight` pinta una barra en rojo y el resto en gris.

    Ese es el uso correcto del acento: destacar **una** categoría. Colorear
    todas las barras de rojo no destaca ninguna.
    """
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    if highlight is None:
        colores = make_n_colors(len(x))
    else:
        colores = [ROJO.hex if i == highlight else GRIS_CLARO.hex for i in range(len(x))]
    (ax.barh if horizontal else ax.bar)(x, y, color=colores)
    ax.grid(axis="x" if horizontal else "y")
    ax.grid(axis="y" if horizontal else "x", visible=False)
    return fig, style_axes(ax, title, subtitle, xlabel, ylabel)


def line_chart(x: Sequence, series: dict, title: str = "", subtitle: str = "",
               xlabel: str = "", ylabel: str = "", figsize: Tuple[float, float] = (10, 5.5),
               ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Líneas. `series` es `{etiqueta: valores}` y conserva el orden de inserción."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    colores = make_n_colors(len(series))
    for (etiqueta, valores), color in zip(series.items(), colores):
        ax.plot(x, valores, label=etiqueta, color=color)
    if len(series) > 1:
        ax.legend(loc="best")
    return fig, style_axes(ax, title, subtitle, xlabel, ylabel)


def dist_chart(data: Sequence, bins: int = 30, title: str = "", subtitle: str = "",
               xlabel: str = "", ylabel: str = "Frecuencia", show_mean: bool = True,
               figsize: Tuple[float, float] = (10, 5.5),
               ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Histograma con la media marcada, que es la lectura que casi siempre falta."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    ax.hist(data, bins=bins, color=TINTA.hex, edgecolor="none", alpha=0.85)
    if show_mean:
        media = float(np.mean(data))
        ax.axvline(media, color=ROJO.hex, linestyle="--", linewidth=1.8)
        ax.text(media, ax.get_ylim()[1] * 0.96, f" media {media:,.2f}",
                color=ROJO.hex, fontsize=TYPE_SCALE.annotation, va="top")
    ax.grid(axis="x", visible=False)
    return fig, style_axes(ax, title, subtitle, xlabel, ylabel)


def scatter_chart(x: Sequence, y: Sequence, title: str = "", subtitle: str = "",
                  xlabel: str = "", ylabel: str = "", hue: Optional[Sequence] = None,
                  figsize: Tuple[float, float] = (8, 6),
                  ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Dispersión. Con `hue` numérico usa el colormap secuencial de marca."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    if hue is None:
        ax.scatter(x, y, color=TINTA.hex, alpha=0.65, edgecolors="none")
    else:
        sc = ax.scatter(x, y, c=hue, cmap=get_cmap("avianca_inks"), alpha=0.85, edgecolors="none")
        fig.colorbar(sc, ax=ax)
    return fig, style_axes(ax, title, subtitle, xlabel, ylabel)


def correlation_heatmap(matrix, labels: Optional[Iterable[str]] = None, title: str = "",
                        subtitle: str = "", figsize: Tuple[float, float] = (8, 7),
                        ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Matriz de correlación con el colormap divergente centrado en cero."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    im = ax.imshow(matrix, cmap=get_cmap("avianca_diverging"), vmin=-1, vmax=1)
    if labels is not None:
        labels = list(labels)
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
        ax.set_yticks(range(len(labels)), labels)
    ax.grid(visible=False)
    fig.colorbar(im, ax=ax, shrink=0.85)
    return fig, style_axes(ax, title, subtitle)


def slice_chart(slices: Sequence[str], baseline: Sequence[float], candidate: Sequence[float],
                metric: str = "MAE", title: str = "", subtitle: str = "",
                lower_is_better: bool = True, figsize: Tuple[float, float] = (10, 6),
                ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Compara candidato contra línea base **por segmento**.

    Es la gráfica que exige el marco: un agregado que mejora puede ocultar
    degradación en un subconjunto. Los segmentos que empeoran salen en rojo, y
    el color nunca va solo — el delta se imprime al lado de cada barra.
    """
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    y = np.arange(len(slices))
    deltas = [c - b for b, c in zip(baseline, candidate)]
    empeora = [(d > 0) if lower_is_better else (d < 0) for d in deltas]

    ax.barh(y - 0.2, baseline, height=0.38, color=GRIS_CLARO.hex)
    ax.barh(y + 0.2, candidate, height=0.38,
            color=[ROJO.hex if e else TEAL.hex for e in empeora])
    ax.set_yticks(y, slices)
    ax.invert_yaxis()

    span = max(max(baseline), max(candidate)) or 1.0
    for i, (c, d, e) in enumerate(zip(candidate, deltas, empeora)):
        signo = "+" if d >= 0 else ""
        ax.text(c + span * 0.01, i + 0.2, f"{signo}{d:,.3f}" + ("  peor" if e else "  mejor"),
                va="center", fontsize=TYPE_SCALE.annotation,
                color=ROJO.hex if e else GRIS_MEDIO.hex)
    # La leyenda nombra los tres significados reales del color. Una sola entrada
    # "Candidato" mentiría: sus barras son rojas o teal según el resultado.
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GRIS_CLARO.hex, label="Línea base"),
                       Patch(color=TEAL.hex, label="Candidato — mejora"),
                       Patch(color=ROJO.hex, label="Candidato — empeora")],
              loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)  # fuera del área de barras: nunca las tapa
    ax.grid(axis="y", visible=False)
    return fig, style_axes(ax, title, subtitle, xlabel=metric)
