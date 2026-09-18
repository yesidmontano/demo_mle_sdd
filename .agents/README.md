# Subagentes de fase

Cada fase del ciclo SDD se materializa en un subagente con **contexto propio, herramientas
restringidas y una única responsabilidad**.

La separación no es cosmética. La regla dura del directorio:

> **El subagente que implementa no es el que aprueba.**

`apply` y `verify` nunca comparten contexto. Verificar en un contexto distinto del que produjo el
candidato es lo que impide que el mismo razonamiento que generó un resultado lo declare
aceptable.

| Agente | Fase | Puede escribir |
|---|---|---|
| `orchestrator` | enruta | nada |
| `explore` | explorar | `changes/<id>/evidence/` |
| `spec` | especificar | `changes/<id>/delta specs` |
| `design` | diseñar | `changes/<id>/design.md` |
| `tasks` | planificar | `changes/<id>/tasks.md` |
| `apply` | implementar | código, `gates/`, modelos |
| `verify` | verificar | `changes/<id>/evidence/` |
| `archive` | archivar | `specs/` (única excepción, y solo con comprobante) |

Ningún agente salvo `archive` escribe en `openspec/specs/`, y un hook del entorno lo impone
fuera del control del modelo.

Asignación de modelo por fase: razonamiento costoso en `design` y `verify`, económico en
`tasks` y `apply`.
