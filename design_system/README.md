# avianca_brand

> Sistema de diseño de Avianca para visualización de datos

Paquete de Python que implementa los design tokens publicados en avianca.com
—colores, tipografía, paletas y estilos— para que toda figura del proyecto salga con la misma
identidad sin decidirlo caso por caso.

## Instalación

```bash
pip install -e design_system
```

## Uso

```python
import avianca_brand as ab

ab.apply_avianca_style()          # una vez, al inicio del script
ab.apply_avianca_style("dark")

with ab.avianca_style("dark"):    # o solo dentro del bloque
    ...
```

## Lo que hay que saber antes de usarlo

**El primario de Avianca es la tinta `#1B1B1B`, no el rojo.** Su propio token
`--logo-avianca-primary` resuelve a ese casi-negro. El rojo `#FF0000` es **acento**: la serie
principal, *una* categoría destacada, o lo que empeora. Usado como color dominante contradice la
marca y además pierde legibilidad —sobre blanco da ~4:1—, así que para texto pequeño está
`ROJO_TEXTO` (`#CC0000`, ~5.3:1).

Por eso la paleta categórica empieza en tinta y sigue en rojo: la serie que el lector debe mirar
primero lleva el acento, y el resto se apoya en neutros y teal. Una paleta que arranca en rojo
obliga a que todo lo demás compita con él.

## Módulos

| Módulo | Qué aporta |
|---|---|
| `colors` | Primarios, secundarios, neutros y semánticos, cada uno con el token de origen |
| `typography` | Red Hat Display / Text / Mono y la escala tipográfica |
| `palettes` | Categóricas, secuenciales y divergentes |
| `styles` | `apply_avianca_style()`, `avianca_style()` y `reset_style()` |
| `charts` | Gráficas con la marca puesta; todas devuelven `(fig, ax)` |
| `layout` | Dashboards, figuras de reporte y filas de KPI |

## Color

| Nombre | HEX | Token | Rol |
|---|---|---|---|
| Tinta | `#1B1B1B` | `--brand-primary` | Primario |
| Rojo | `#FF0000` | `--red-500` | Acento de marca |
| Rojo Texto | `#CC0000` | `--red-600` | Acento accesible |
| Rojo Profundo | `#990000` | `--red-700` | Secundario |
| Teal | `#0190A0` | `--link-color-secondary` | Contraste frío |
| Texto | `#131313` | `--text-color` | Neutro |
| Gris Medio | `#5A5A5A` | `--text-brand-disable` | Neutro |
| Gris Claro | `#D9D9D9` | `--state-disabled` | Neutro |
| Papel | `#F8F8F8` | `--light-color` | Fondo |

## Gráficas

`bar_chart` · `line_chart` · `dist_chart` · `scatter_chart` · `correlation_heatmap` ·
**`slice_chart`** · `create_dashboard` · `create_report_figure` · `create_kpi_figure`

`slice_chart` es la que exige el marco SDD: compara candidato contra línea base **por segmento**,
porque un agregado que mejora puede ocultar degradación en un subconjunto. Pinta en rojo lo que
empeora, en teal lo que mejora, y **escribe el delta con su signo al lado de cada barra** — el
color nunca comunica solo.

```python
fig, ax = ab.slice_chart(
    slices=["Business", "Economy", "Alta demanda"],
    baseline=[8.1, 5.4, 9.9],
    candidate=[8.9, 5.0, 9.1],
    metric="MAE",
    title="MAE por segmento",
)
```

## Tipografía

Red Hat Display es la fuente real de avianca.com y está en Google Fonts. Si no está instalada,
Matplotlib cae a los fallbacks sin fallar.

```bash
brew install --cask font-red-hat-display font-red-hat-text
```

## Logo

`avianca_brand/assets/logo.svg` es la fuente de verdad. `add_logo()` necesita un PNG —Matplotlib
no rasteriza SVG—, así que si solo existe el SVG la función no hace nada y **no falla**: una
figura no se pierde por un asset.

## Figuras multi-panel

Para más de un panel usa `create_dashboard(nrows, ncols, title=..., subtitle=...)`, **no**
`plt.subplots` + `fig.suptitle`: `suptitle` no reserva espacio y pisa los títulos de los paneles.
La cabecera de `create_dashboard` se mide en pulgadas (no en fracción de la figura), así que
funciona igual en figuras bajas y altas, y deja separación entre filas para que las etiquetas
del eje x no toquen el título del panel siguiente. Los paneles llevan `ax.set_title(...)` propio.
