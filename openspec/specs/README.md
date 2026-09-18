# Main specs — el Spec Pack vigente

Refleja **lo que está en producción**. Ninguna feature edita este directorio: escribe un delta
bajo `openspec/changes/<change>/specs/` y la fusión ocurre al sincronizar o archivar. Un hook lo
impone.

## Capabilities de un modelo

El Spec Pack de un modelo es el conjunto de capabilities que comparten su prefijo. Ocho aspectos,
en este orden, porque cada uno restringe al siguiente:

| Capability | Gobierna |
|---|---|
| `<modelo>-problem` | objetivo de negocio vs objetivo de ML, métrica de decisión, no-objetivos |
| `<modelo>-data` | esquema, tipos, rangos, nulabilidad, PII, frescura, linaje |
| `<modelo>-features` | definición point-in-time, fuente offline/online, paridad train/serve |
| `<modelo>-training` | dataset, splits, semilla, hiperparámetros, reproducibilidad |
| `<modelo>-evaluation` | umbrales por slice, tests de comportamiento, calibración, baseline |
| `<modelo>-serving` | esquema E/S, p99, versionado, degradación, trazabilidad |
| `<modelo>-monitoring` | señales, ventanas, umbrales, severidad y acción |
| `<modelo>-governance` | tier de riesgo, aprobadores, retención, rollback |

Ejemplo: `openspec/specs/fare-forecast-evaluation/spec.md`.
Plantilla: `openspec/templates/capability.spec.md`.

## Por qué markdown con un bloque `yaml contract`

El formato de requisitos y escenarios es el de OpenSpec, así que `openspec validate`,
`openspec-sync-specs` y `openspec archive` funcionan sin adaptaciones.

Pero un requisito en prosa no puede fallar, y **una spec que no puede fallar no gobierna nada**.
Por eso cada requisito lleva dentro un bloque ` ```yaml contract ` con su recorte comprobable: el
umbral, el esquema o el invariante que un gate ejecuta. El escenario lo lee una persona; el
bloque lo lee `gates/`.

Un requisito sin bloque `contract` debe declarar `non_binding: true` de forma explícita, para que
nadie lo confunda con una garantía.
