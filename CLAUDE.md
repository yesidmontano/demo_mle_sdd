# demo_mle_sdd — MLOps gobernado por especificaciones

Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**. Se monta sobre
[OpenSpec](https://github.com/Fission-AI/OpenSpec) —su CLI, su estructura y sus verbos— y le
añade la capa que ML necesita.

## La idea en una página

SDD nació para gobernar **código**, que cabe entero en un pull request. En ML el comportamiento
lo producen **tres artefactos** —código, datos y modelo entrenado— y solo uno pasa por revisión
de pares. Por eso aquí la especificación se extiende a los tres, bajo una regla dura:

> **Toda spec es ejecutable.** Si un requisito no desciende a un contrato comprobable y de ahí a
> un gate con capacidad de bloqueo, no gobierna nada: es documentación. Se marca `non_binding`.

### Dos ciclos ortogonales

- **Ciclo macro — ciclo de vida ML**: Negocio → Datos → Preparación → Modelado → Evaluación →
  Despliegue → **Operación y monitoreo**. Iterativo, no lineal, y no termina.
- **Ciclo micro — SDD**: explorar → proponer → especificar → diseñar → planificar →
  implementar → verificar → archivar.

**SDD no es una fase del ciclo de vida.** Cada fase macro contiene N *changes* y cada uno recorre
el ciclo SDD completo. No todo change despliega: un análisis archiva un hallazgo; un experimento
fallido, un resultado negativo con su evidencia.

## Estructura

```
openspec/
  config.yaml                          tiers, gate_routing y rules por fase
  specs/<modelo>-<aspecto>/spec.md     main specs — el Spec Pack vigente
  changes/<change>/
    proposal.md  design.md  tasks.md
    specs/<modelo>-<aspecto>/spec.md   delta specs (ADDED/MODIFIED/REMOVED/RENAMED)
    evidence/                          seal.json · receipt.json · salidas de gates
  changes/archive/                     changes cerrados
code/<fase>/                           scripts .py, una subcarpeta por fase
data/{bronze,silver,gold}/             capas de datos
results/<fase>/                        salidas por fase: .md, .png, tablas
gates/                                 los contratos, ejecutables
design_system/                         avianca_brand — paquete de marca (pip -e)
.claude/agents/                        mle-sdd-orquestador + subagentes de fase
.claude/skills/                        el flujo SDD-MLOps
.claude/hooks/                         lo que el entorno impone, fuera del control del agente
```

### Los ocho aspectos

Una capability se nombra `<modelo>-<aspecto>`. El Spec Pack de un modelo es el conjunto que
comparte prefijo.

`problem` · `data` · `features` · `training` · `evaluation` · `serving` · `monitoring` ·
`governance`

### Por qué markdown con un bloque `yaml contract`

El formato de requisitos y escenarios es el de OpenSpec, así que `openspec validate`, la
sincronización y el archivado funcionan sin adaptaciones. Pero un requisito en prosa no puede
fallar, así que cada uno lleva dentro un bloque ` ```yaml contract ` con su umbral, esquema o
invariante. El escenario lo lee una persona; el bloque lo ejecuta un gate.

## Reglas del repositorio

1. **Ninguna feature edita `openspec/specs/` directamente.** Escribe delta specs en el change; la
   fusión ocurre al sincronizar o archivar, y solo con comprobante. Un hook lo impone.
2. **Los gates se derivan del aspecto de las capabilities que toca el delta**, no de la fase del
   ciclo de vida:

   | Aspecto | Gates |
   |---|---|
   | `data` | `data-contract`, `freshness` |
   | `features` | `train-serve-parity`, `leakage-check` |
   | `training` | `reproducibility`, `compute-budget` |
   | `evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` |
   | `serving` | `contract-compat`, `latency-p99`, `rollback-drill` |
   | `monitoring` | `alert-backtest`, `false-positive-budget` |
   | `problem`, `governance` | `human-review` |

3. **Congelar antes de leer.** El candidato se sella y solo entonces se evalúa, de modo que la
   evidencia pertenece a la versión exacta que se promueve.
4. **Proporcionalidad.** Un change de alcance reducido recorre la vía abreviada. El tier fija el
   corte. Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos
   marcos.
5. **El comprobante es el objeto de promoción**, no un permiso. Liga cinco identidades:
   `spec_pack + dataset + código + entorno + modelo`.

## Flujo de trabajo

| Fase | Skill | Equivalente OpenSpec |
|---|---|---|
| Inicializar el proyecto y el Spec Pack de un modelo | `sdd-init` | — (capa ML) |
| Investigar datos, fuentes y viabilidad | `sdd-explore` | `openspec-explore` |
| Redactar la propuesta del change | `sdd-propose` | `openspec-propose` |
| Traducirla a delta specs ejecutables | `sdd-spec` | `openspec-propose` (artefacto `specs`) |
| Decidir la arquitectura | `sdd-design` | — (artefacto `design`) |
| Descomponer en tareas | `sdd-tasks` | — (artefacto `tasks`) |
| Implementar y sellar el candidato | `sdd-apply` | `openspec-apply-change` |
| Correr los gates y emitir el comprobante | `sdd-verify` | — (capa ML) |
| Fusionar deltas y cerrar el change | `sdd-archive` | `openspec-sync-specs` + `openspec-archive-change` |

`sdd-verify` no tiene equivalente porque en software se va de `apply` a `archive`: el artefacto
gobernado se revisa leyéndolo. En ML **hay que medirlo**, y el comprobante existe porque "la misma
versión" no la define el commit. `sdd-archive` absorbe la sincronización: las main specs no se
tocan sin comprobante, así que separar los dos pasos solo abriría una puerta sin guardia.

## Subagentes

Viven en `.claude/agents/`, que es donde el harness de Claude Code los descubre solo. El
orquestador es **`mle-sdd-orquestador`**: enruta cada change por el ciclo y no implementa nada.

| Agente | Fase | Puede escribir |
|---|---|---|
| `mle-sdd-orquestador` | orquesta y enruta | nada |
| `sdd-explore` | explorar | `changes/<id>/evidence/` |
| `sdd-propose` | proponer | `changes/<id>/proposal.md` |
| `sdd-spec` | especificar | delta specs del change |
| `sdd-design` | diseñar | `changes/<id>/design.md` |
| `sdd-tasks` | planificar | `changes/<id>/tasks.md` |
| `sdd-apply` | implementar | código, `gates/`, modelos |
| `sdd-verify` | verificar | `changes/<id>/evidence/` |
| `sdd-archive` | archivar | `specs/` (única excepción, y solo con comprobante) |

Ningún agente salvo `sdd-archive` escribe en `openspec/specs/`, y un hook lo impone fuera del
control del modelo.

**Regla de separación: el subagente que implementa no es el que aprueba.** `sdd-apply` y
`sdd-verify` nunca comparten contexto — verificar en un contexto distinto del que produjo el
candidato es lo que impide que el mismo razonamiento que generó un resultado lo declare
aceptable.

Asignación de modelo por fase: razonamiento costoso en `sdd-design` y `sdd-verify`, económico en
`sdd-tasks` y `sdd-apply`.

## Políticas del repositorio

### Idioma de los documentos de OpenSpec

**Todo lo que vive bajo `openspec/` se escribe en español**: `proposal.md`, `design.md`,
`tasks.md`, delta specs y main specs. Esta decisión prevalece sobre el «inglés por defecto» que
mencionan las skills `sdd-*`.

- Se mantienen en su forma original las palabras clave que el CLI de OpenSpec parsea:
  `## ADDED/MODIFIED/REMOVED Requirements`, `### Requirement:`, `#### Scenario:`, `SHALL`,
  `WHEN`, `THEN`, y los encabezados `## Why`, `## What Changes`, `## Capabilities`, `## Impact`
  de la propuesta.
- Los identificadores (nombres de capability, columnas, gates, claves del bloque
  `yaml contract`) no se traducen.

### Formato de archivo: solo `.py`

**El único formato de código admitido es `.py`.** Nada de notebooks en el flujo gobernado.

La razón no es estética. Un notebook guarda estado oculto y orden de ejecución arbitrario, así que
dos personas ejecutando el mismo `.ipynb` obtienen resultados distintos sin que nada lo señale.
Eso rompe de raíz el sellado del candidato: no se puede congelar algo cuyo resultado depende del
orden en que alguien pulsó las celdas.

La exploración vive en un change y su conclusión se archiva como hallazgo (`sdd-explore`), no en
un notebook suelto.

### Carpetas

| Carpeta | Regla |
|---|---|
| `code/<fase>/` | Una subcarpeta por fase del ciclo de vida. Scripts ejecutables **desde la raíz del repositorio**, no desde su propia carpeta |
| `data/bronze/` | Datos crudos tal como llegaron. **Inmutables**: ningún script escribe aquí |
| `data/silver/` | Limpios y validados contra el contrato de `<modelo>-data`. Derivados y reproducibles |
| `data/gold/` | Listos para entrenar o servir: agregados, features materializadas |
| `results/<fase>/` | Salidas por fase: markdown y tablas. Lo que se lee, no lo que se ejecuta |
| `results/<fase>/imgs/` | **Toda imagen y gráfico** de la fase, sin excepción. El markdown de `results/<fase>/` los referencia con ruta relativa |

Las tres capas de datos son derivaciones, no copias: **si `silver` no se puede regenerar desde
`bronze` con el código del repositorio, la capa está rota.** Solo `bronze` se versiona fuera del
repositorio; `silver` y `gold` se reconstruyen.

### Análisis visual

**Todo análisis y toda decisión se acompañan de una figura** que la respalde: la conclusión
escrita cita la figura y la figura se lee sin necesidad del texto. Una decisión de datos o de
modelo sin evidencia visual es una afirmación, no un hallazgo. Las figuras se guardan en
`results/<fase>/imgs/` y usan el sistema de marca (ver «Convenciones de código»).

### MLflow: obligatorio, con signature y flavor

**Todo entrenamiento y todo experimento se registra en MLflow.** Un modelo que no pasó por MLflow
no existe para el marco, y no puede sellarse ni promoverse.

Dos exigencias que no son opcionales:

```python
import mlflow
from mlflow.models import infer_signature

with mlflow.start_run(run_name=f"{modelo}/{change_id}"):
    mlflow.log_params(params)
    mlflow.log_metrics(metricas_globales)
    mlflow.log_metrics(metricas_por_slice)      # el agregado solo no basta

    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(                   # el flavor que corresponda
        sk_model=model,
        name="model",
        signature=signature,                    # OBLIGATORIA
        input_example=X_train.head(5),
    )
```

- **`signature` siempre.** Es el contrato de entrada y salida del modelo, verificable en tiempo de
  carga. Sin ella, el esquema declarado en `<modelo>-serving` no tiene con qué contrastarse y el
  gate `contract-compat` no puede fallar — es decir, deja de ser un gate.
- **Flavor explícito.** `mlflow.sklearn`, `mlflow.xgboost`, `mlflow.pyfunc`… nunca un pickle
  suelto. El flavor es lo que permite cargar el modelo sin reconstruir su entorno a mano.
- **Métricas por slice, no solo agregadas.** Los mismos segmentos que declara
  `<modelo>-evaluation`.
- El `run_id` de MLflow entra en el comprobante junto a los cinco hashes. Es el puente entre la
  evidencia del marco y el registro del experimento.

### Convenciones de código

- **Python 3.12**, en el `.venv` de la raíz del repositorio. Actívalo antes de ejecutar nada:
  `source .venv/bin/activate`. No crees entornos paralelos ni instales con el Python del sistema:
  el entorno forma parte de lo que se sella, y un candidato entrenado fuera de él no es
  reproducible.
- Rutas relativas a la raíz del repositorio. Un script que solo funciona desde su propia carpeta
  no es reproducible.
- Los gates viven en `gates/` y son ejecutables independientes: entran por CLI, salen con código 0
  (pasa) o distinto de 0 (bloquea) y un JSON en stdout.
- Semilla y entorno fijados según la capability `training`.
- **Toda figura usa el sistema de marca**: `pip install -e design_system` y
  `avianca_brand.apply_avianca_style()` al inicio del script. Para comparar candidato contra línea
  base por segmento está `slice_chart`, que es la gráfica que el marco exige.
