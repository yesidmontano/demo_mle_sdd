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
- **Ciclo micro — SDD (OpenSpec)**: explorar → proponer (`proposal`, `specs`, `design`, `tasks`) →
  implementar (sellar el candidato) → verificar (gates) → archivar.

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
data/{bronze,silver,gold}/             capas de datos (silver = feature store, gold = inferencia)
results/<fase>/                        salidas por fase: .md y tablas; figuras en results/<fase>/imgs/
gates/                                 los contratos, ejecutables, con sus tests
design_system/                         avianca_brand — paquete de marca (pip -e)
.claude/commands/opsx/                 /opsx:explore · propose · apply · verify · sync · archive
.claude/skills/openspec-*/             las skills de OpenSpec que respaldan esos comandos
.claude/agents/                        mle-sdd-orquestador + un subagente opsx-* por paso
.claude/hooks/                         lo que el entorno impone, fuera del control del agente
mlflow.db · mlartifacts/               seguimiento y artefactos locales de MLflow (no se versionan)
```

Hooks activos (`.claude/settings.json`): `spec_pack_guard.py` bloquea la escritura directa en
`openspec/specs/`, y `sdd_phase_guard.py` comprueba las precondiciones de cada paso al despachar un subagente
`opsx-*` (ver «Subagentes»).

### Los ocho aspectos

Una capability se nombra `<modelo>-<aspecto>`. El Spec Pack de un modelo es el conjunto que
comparte prefijo.

`problem` · `data` · `features` · `training` · `evaluation` · `serving` · `monitoring` ·
`governance`

El tier de `openspec/config.yaml` decide cuáles aplican. `conversion-sesion` es **Tier 2**
(`problem`, `data`, `features`, `evaluation`, `serving`, `monitoring`): `training` y `governance` no se
especifican, y las exigencias de entrenamiento (MLflow, semilla, sellado) viven en el diseño de cada
change y en los gates de evaluación.

### Por qué markdown con un bloque `yaml contract`

El formato de requisitos y escenarios es el de OpenSpec, así que `openspec validate`, la
sincronización y el archivado funcionan sin adaptaciones. Pero un requisito en prosa no puede
fallar, así que cada uno lleva dentro un bloque ` ```yaml contract ` con su umbral, esquema o
invariante. El escenario lo lee una persona; el bloque lo ejecuta un gate.

## Reglas del repositorio

1. **Ninguna feature edita `openspec/specs/` directamente.** Escribe delta specs en el change; la
   fusión ocurre al sincronizar o archivar, y solo con comprobante. El hook `spec_pack_guard.py`
   bloquea la escritura directa con las herramientas de edición. **`openspec archive` corre por shell
   y no verifica el comprobante**: compruébalo tú antes de archivar un change que promueve un modelo.
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

   Implementados en `gates/`: `data-contract`, `leakage-check`, `train-serve-parity`, `slice-eval`,
   `behavioral-tests`, `incumbent-rerun`, `contract-compat`, `latency-p99`, `rollback-drill`,
   `alert-backtest`, `false-positive-budget`. Sin ejecutable: `freshness` (`non_binding`, el dataset no
   tiene fecha), `reproducibility` y `compute-budget` (aspecto `training`, fuera del Tier 2) y
   `human-review`, que es evidencia manual (`evidence/human-review.json`) de una persona.

3. **Congelar antes de leer.** El candidato se sella (`gates/seal.py`) y solo entonces se evalúa, de modo
   que la evidencia pertenece a la versión exacta que se promueve. El sello no se sobrescribe. Si algo
   del código de entrenamiento cambia después de sellar, hay que volver a entrenar y re-sellar **antes**
   de leer ninguna métrica de test.
4. **Proporcionalidad.** Un change de alcance reducido recorre la vía abreviada. El tier fija el
   corte. Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos
   marcos.
5. **El comprobante es el objeto de promoción**, no un permiso. Liga cinco identidades:
   `spec_pack + dataset + código + entorno + modelo` (más el `run_id`). `gates/receipt.py` lo emite y
   `code/06-deploy/promote.py` lo exige para asignar `champion`.
6. **Los gates recalculan, no leen resultados ajenos.** Cargan el modelo o el dataset y calculan; un gate
   que confía en un archivo que él no produjo no puede fallar. Leen su criterio del bloque `yaml contract`
   del change (`--change <id>`) o, si ya se archivó, de las main specs (`_contracts.load_any`). Cada
   gate tiene un test con un caso en que falla.

## Flujo de trabajo

Cada unidad de trabajo es un **change de OpenSpec**. Los comandos (`.claude/commands/opsx/`) y sus skills
(`.claude/skills/openspec-*`) son los de OpenSpec; la capa de ML se añade en el contenido del change:

| Paso | Comando | Qué hacer en este marco |
|---|---|---|
| Pensar antes de comprometer | `/opsx:explore` | Investigar datos, fuentes y viabilidad; un hallazgo se archiva como evidencia, no como notebook |
| Proponer | `/opsx:propose` | Genera `proposal`, delta `specs` (con bloques `yaml contract`), `design` y `tasks`. La propuesta declara objetivo de negocio y de ML por separado, no-objetivos y la alternativa descartada |
| Implementar | `/opsx:apply` | Ejecuta las tareas: código y sellado del candidato **antes** de evaluar |
| Verificar | `/opsx:verify` | Coherencia del change (completitud, corrección, coherencia) **y** los gates que activa el alcance, con su evidencia en `evidence/`; si el change promueve un modelo, el comprobante |
| Fusionar sin archivar | `/opsx:sync` | Aplica los deltas a las main specs |
| Cerrar | `/opsx:archive` | Fusiona los deltas y mueve el change a `archive/`; si el change promueve un modelo, comprobar el comprobante antes (regla 1) |

Cada fase del ciclo de vida contiene N changes; un change puede cubrir varias fases contiguas si es
pequeño (el primero cubrió 01–03). El tier fija cuánto ciclo se recorre.

## Subagentes

Viven en `.claude/agents/`, donde el harness los descubre solo. Cada uno envuelve una skill de OpenSpec y le
añade la capa de ML; el orquestador enruta y no implementa nada.

| Agente | Skill de OpenSpec | Puede escribir |
|---|---|---|
| `mle-sdd-orquestador` | — | nada |
| `opsx-explore` | `openspec-explore` | hallazgos (sin contrato ni código de producción) |
| `opsx-propose` | `openspec-propose` | los artefactos del change: proposal, delta specs, design, tasks |
| `opsx-apply` | `openspec-apply-change` | código, `gates/`, `results/`, modelos |
| `opsx-verify` | `openspec-verify-change` | `evidence/` (lo escriben los gates) |
| `opsx-archive` | `openspec-archive-change` + `openspec-sync-specs` | `openspec/specs/` (única excepción) |

`sdd_phase_guard.py` bloquea el despacho de un paso si falta su precondición: `opsx-apply` y `opsx-verify`
exigen `tasks.md`; `opsx-verify` exige `evidence/seal.json` si el delta toca `evaluation`; `opsx-archive` exige
`evidence/receipt.json` si el delta toca `serving`. Falla en abierto ante la duda.

**El que implementa no aprueba.** `opsx-apply` y `opsx-verify` nunca comparten contexto. La aprobación no la da el razonamiento que produjo el resultado: la dan
los **gates** (que recalculan desde los artefactos) y, para `problem` y `governance`, **una persona**
(`human-review`). Un gate que no puede fallar es un hallazgo, no un gate.

## Políticas del repositorio

### Idioma de los documentos de OpenSpec

**Todo lo que vive bajo `openspec/` se escribe en español**: `proposal.md`, `design.md`,
`tasks.md`, delta specs y main specs. Esta decisión prevalece sobre cualquier default en inglés de
las plantillas o skills.

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

La exploración vive en un change y su conclusión se archiva como hallazgo (`/opsx:explore`), no en
un notebook suelto.

### Carpetas

| Carpeta | Regla |
|---|---|
| `code/<fase>/` | Una subcarpeta por fase del ciclo de vida. Scripts ejecutables **desde la raíz del repositorio**, no desde su propia carpeta |
| `data/bronze/` | Datos crudos tal como llegaron. **Inmutables**: ningún script escribe aquí |
| `data/silver/` | **Feature store.** Dataset limpio y validado, split `train`/`test` (limpios y transformados), pipeline de preprocesamiento ajustado (`.joblib`) y `manifest.json` con semilla, conteos y hashes. Derivados y reproducibles |
| `data/gold/` | **Solo inferencia**: `data/gold/inferences/` guarda una fila por sesión servida (versión del modelo, entradas `in_*`, probabilidad, decisión, latencia, estado). Ningún dataset de entrenamiento ni de evaluación. No se versiona |
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

### Preparación de datos: orden del proceso

Limpieza y formateo → **split train/test** → feature engineering. El split va **siempre antes**
del feature engineering: las transformaciones que aprenden de los datos (escalado, target
encoding) se ajustan solo con `train` y se aplican a `test`. El pipeline se define en su propio
módulo (`code/03-data_preparation/preprocessing.py`), separado del script que lo ejecuta, para
que serving lo reutilice tal cual.

### Despliegue y monitoreo (simulados en local)

No hay nube: el «despliegue» es una función con comando y el «monitoreo» un dashboard HTML.

```bash
python code/06-deploy/register_model.py            # registra v1 (línea base, rollback) y v2 (candidato sellado)
python code/06-deploy/promote.py --version 2       # asigna `champion`; exige comprobante (receipt.json)
python code/06-deploy/predict.py                   # 3 sesiones al azar, alias champion -> data/gold/inferences/
python code/06-deploy/predict.py --model-version 1 # la versión del modelo es un parámetro, no código
python code/06-deploy/simulate_traffic.py --batches 300 --drift-from-batch 220 --reset   # source = simulation
python code/07_operation_and_monitoring/build_dashboard.py   # results/07_operation_and_monitoring/dashboard.html
```

- El modelo servido siempre es una **versión registrada** en MLflow (`mlflow.pyfunc`, con `signature`); cada
  inferencia guarda su versión y `run_id`. Rollback = `promote.py --version <anterior>`.
- **`champion` solo se asigna con comprobante** que ligue spec pack, dataset, código, entorno, modelo y `run_id`
  con todos los gates en verde.
- Cada inferencia guarda las **entradas** (`in_*`): son la base del data drift. El tráfico simulado se marca
  `source = simulation`; nunca se presenta como tráfico real.
- El dashboard se genera desde Gold con `drift.py`, la misma lógica de alertas que usan los gates `alert-backtest`
  y `false-positive-budget`.

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
- **El modelo registrado es un `Pipeline` completo** (preprocesamiento ya ajustado + clasificador): la
  entrada es la sesión cruda, no features transformadas. Se sirve con `mlflow.pyfunc` para que la
  `signature` se aplique, y con `pyfunc_predict_fn="predict_proba"`.
- **Seguimiento local en SQLite** (`sqlite:///mlflow.db`, artefactos en `mlartifacts/`): MLflow 3.x ya no
  admite el file store `mlruns/`. Ninguno de los dos se versiona. MLflow serializa sklearn con `skops` y
  exige declarar los tipos propios (`skops_trusted_types`).
- El **Model Registry** guarda `conversion-sesion` con versiones y alias; las etiquetas de cada versión
  llevan `run_id`, `role`, `k_fraction` y `decision_threshold`.

### Convenciones de código

- **Python 3.12**, en el `.venv` de la raíz del repositorio. Actívalo antes de ejecutar nada:
  `source .venv/bin/activate`. No crees entornos paralelos ni instales con el Python del sistema:
  el entorno forma parte de lo que se sella, y un candidato entrenado fuera de él no es
  reproducible.
- Rutas relativas a la raíz del repositorio. Un script que solo funciona desde su propia carpeta
  no es reproducible.
- Los gates viven en `gates/` y son ejecutables independientes: entran por CLI, salen con código 0
  (pasa) o distinto de 0 (bloquea) y un JSON en stdout.
- Semilla fija (`preprocessing.SEED = 42`) y entorno registrado en el sello: sin `training` en el Tier 2, el
  determinismo lo comprueba `incumbent-rerun` (reentrenar la línea base reproduce su log-loss).
- **Toda figura usa el sistema de marca**: `pip install -e design_system` y
  `avianca_brand.apply_avianca_style()` al inicio del script. Para comparar candidato contra línea
  base por segmento está `slice_chart`, que es la gráfica que el marco exige.
- **Figuras con varios paneles: `create_dashboard(...)`, nunca `plt.subplots` + `fig.suptitle`.**
  `suptitle` no reserva espacio y pisa los títulos de los paneles.
- **Un HTML que usa JavaScript no se ve desde `file://` en el panel del navegador**: sírvelo con
  `python -m http.server` para revisarlo. El dashboard de monitoreo lee Gold en su paso de construcción
  (`build_dashboard.py`), no en el navegador.
