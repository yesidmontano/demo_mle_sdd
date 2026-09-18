# demo_mle_sdd — MLOps gobernado por especificaciones

Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**: las especificaciones y
los contratos gobiernan entrenamiento, validación, registro y promoción.

## La idea en una página

SDD nació para gobernar **código**, que cabe entero en un pull request. En ML el comportamiento
lo producen **tres artefactos** —código, datos y modelo entrenado— y solo uno pasa por revisión
de pares. Por eso aquí la especificación se extiende a los tres, bajo una regla dura:

> **Toda spec es ejecutable.** Si un requisito no desciende a contrato y de ahí a un gate con
> capacidad de bloqueo, no gobierna nada: es documentación. Se marca `non_binding`.

### Dos ciclos ortogonales

- **Ciclo macro — ciclo de vida ML**: Negocio → Datos → Preparación → Modelado → Evaluación →
  Despliegue → **Operación y monitoreo**. Iterativo, no lineal, y no termina.
- **Ciclo micro — SDD**: explorar → proponer → especificar → diseñar → planificar → implementar
  → verificar → archivar.

**SDD no es una fase del ciclo de vida.** Cada fase macro contiene N *features* (un análisis, un
experimento, una fuente nueva, un umbral nuevo, un cambio de contrato de API) y **cada feature
recorre el ciclo SDD completo**. No toda feature termina en despliegue: un análisis archiva un
hallazgo; un experimento fallido archiva un resultado negativo con su evidencia.

## Estructura

```
openspec/
  config.yaml              política por fase (rules.*) y runner de pruebas
  specs/<modelo>/          Spec Pack vigente — refleja lo que está en producción
    00-problem.yaml        objetivo de negocio vs objetivo ML, métrica de decisión, no-objetivos
    10-data.yaml           esquema, tipos, rangos, nulabilidad, PII, frescura, linaje
    20-features.yaml       definición point-in-time, fuente offline/online, paridad train/serve
    30-training.yaml       dataset, splits, semilla, hiperparámetros, reproducibilidad
    40-evaluation.yaml     umbrales por slice, tests de comportamiento, calibración, baseline
    50-serving.yaml        esquema E/S, p99, versionado, fallback, trazabilidad
    60-monitoring.yaml     señales, ventanas, umbrales, severidad y acción
    70-governance.yaml     tier de riesgo, aprobadores, retención, rollback
  changes/<feature-id>/    feature en vuelo
    proposal.md  spec.delta.yaml  design.md  tasks.md  evidence/
gates/                     implementación ejecutable de cada gate
.agents/                   subagentes de fase
.claude/skills/            skills del flujo SDD-MLOps
.claude/hooks/             los gates que el entorno ejecuta, fuera del control del agente
```

## Reglas del repositorio

1. **Ninguna feature edita `openspec/specs/` directamente.** Escribe un `spec.delta.yaml` bajo
   `openspec/changes/<feature-id>/`. La fusión ocurre **solo al archivar**. Un hook lo impone.
2. **Los gates se derivan del alcance del delta**, no de la fase en que se sitúa la feature:

   | Documento que toca el delta | Gates que se activan |
   |---|---|
   | `10-data` | contrato de datos: esquema, rangos, nulabilidad, frescura |
   | `20-features` | paridad train/serve + chequeo de fuga temporal |
   | `30-training` | reproducibilidad (semilla, entorno) y presupuesto de cómputo |
   | `40-evaluation` | reejecución sobre el modelo **vigente** + tests de comportamiento |
   | `50-serving` | compatibilidad de contrato + p99 + ensayo de reversión |
   | `60-monitoring` | backtest de la alerta sobre incidentes históricos |
   | `00-problem`, `70-governance` | revisión humana según el tier |

3. **Congelar antes de leer.** El candidato se sella y solo entonces se evalúa, de modo que la
   evidencia pertenece a la versión exacta que se promueve.
4. **Proporcionalidad.** Una feature de alcance reducido recorre la vía abreviada (propuesta +
   evidencia, sin design ni tasks formales). El tier en `70-governance` fija el corte. Imponer el
   ciclo completo a todo el trabajo es el modo de fallo característico de estos marcos.
5. **El comprobante es el objeto de promoción**, no un permiso. Liga cinco identidades:
   `hash(spec_pack) + hash(dataset) + hash(código) + hash(entorno) + hash(modelo)`.

## Flujo de trabajo

| Quiero… | Skill |
|---|---|
| Crear o revisar el Spec Pack de un modelo | `sdd-spec-pack` |
| Abrir una feature como delta | `sdd-delta` |
| Saber y correr los gates que aplican | `sdd-gates` |
| Sellar el candidato y emitir el comprobante | `sdd-receipt` |
| Fusionar el delta y archivar | `sdd-archive` |

Los subagentes de `.agents/` cubren cada fase del ciclo micro. Regla de separación: **el
subagente que implementa no es el que aprueba.** `apply` y `verify` nunca son el mismo contexto.

## Convenciones de código

- Python 3.11+. Dependencias con `uv` si está disponible, si no `pip` en un venv local.
- Los gates viven en `gates/` y son ejecutables independientes: entran por CLI, salen con
  código 0 (pasa) o distinto de 0 (bloquea) y un JSON en stdout.
- Nada de notebooks en el flujo gobernado. La exploración vive en `changes/<id>/` y su
  conclusión se archiva como hallazgo.
