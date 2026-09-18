# demo_mle_sdd — MLOps gobernado por especificaciones

> Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**: las especificaciones y los
> contratos gobiernan datos, entrenamiento, evaluación, registro, promoción y monitoreo.
>
> Caso de uso: **modelo conversión de sesión** sobre datos públicos de reservas de British
> Airways. Recorre las siete fases, del entendimiento del negocio al monitoreo, con el despliegue
> y el monitoreo **simulados en local** (sin nube).

---

## El problema que resuelve

Un equipo que entrena, valida, registra y promueve modelos a mano tiene un síntoma visible —baja
velocidad— y un problema subyacente distinto: **ausencia de trazabilidad**. No existe un artefacto
que responda, meses después y sin preguntarle a nadie, *por qué este modelo está en producción,
contra qué datos se validó y bajo qué criterio se aprobó*.

Hay además una pérdida menos evidente: el trabajo exploratorio que no culmina en despliegue —la
mayor parte del esfuerzo— no deja registro, así que se repiten investigaciones ya hechas.

SDD nació para gobernar **código**, que cabe entero en un pull request. En ML el comportamiento lo
producen **tres artefactos** —código, datos y modelo entrenado— y solo uno pasa por revisión de
pares. Este repositorio extiende la especificación a los tres bajo una regla dura:

> **Toda spec es ejecutable.** Si un requisito no desciende a un contrato comprobable y de ahí a un
> gate con capacidad de bloqueo, no gobierna nada: es documentación.

Se monta sobre [OpenSpec](https://github.com/Fission-AI/OpenSpec) (su CLI, su estructura y sus
verbos) y le añade lo que ML necesita: un bloque ` ```yaml contract ` dentro de cada requisito, gates
ejecutables, sellado del candidato y comprobante de promoción. La explicación completa del marco
está en [`CLAUDE.md`](CLAUDE.md).

---

## Quick path

```bash
# 1. Entorno — Python 3.12. El .venv es local y no se versiona; créalo si no lo tienes:
#    python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e design_system          # sistema de marca Avianca

# 2. Datos (requiere credenciales de Kaggle en ~/.kaggle/kaggle.json)
kaggle datasets download -d anandshaw2001/airlines-booking-csv -p data/bronze --unzip

# 3. Fases de datos: perfil, limpieza, split y feature engineering (todo desde la raíz)
python code/01-business_understanding/problem_figure.py
python code/02-data_understanding/profile.py
python code/03-data_preparation/run_preparation.py     # deja el feature store en data/silver/

# 4. Verificar
openspec list --specs                 # las 6 capabilities del Spec Pack
python -m pytest -q gates             # tests de los gates
python gates/data_contract.py --change <id>
```

Las fases 04–07 (entrenar, evaluar, registrar, servir y monitorear) se ejecutaron dentro de sus
changes; sus comandos están en [Despliegue y monitoreo](#despliegue-y-monitoreo-simulados) y en los
informes de `results/`. Repetir 04–05 desde cero exige abrir un change nuevo que declare la regla de
decisión (`train.py` y `evaluate.py` reciben `--change` y leen K de su spec).

---

## El caso: conversión de sesión

**Modelo `conversion-sesion`** — estima la probabilidad de que una sesión de reserva termine en
compra, para decidir **sobre qué sesiones intervenir**.

### La decisión de negocio

El presupuesto de intervención es finito: un recordatorio, un descuento o una campaña de
retargeting cuestan dinero y desgastan al cliente si se aplican a todo el mundo. La pregunta
operativa es a qué sesiones vale la pena dedicarlos.

El modelo produce un ranking; **la decisión la produce un umbral**, y ese umbral es una cláusula de
`conversion-sesion-evaluation` —intervenir el **20 % superior** del ranking—, no una constante en el
código. Cambiarlo es un change con su gate, no un ajuste silencioso.

| | |
|---|---|
| **Objetivo de negocio** | Ingreso incremental por sesión intervenida, dentro de un presupuesto fijo |
| **Objetivo de ML** | `P(booking_complete \| atributos de la sesión)`, probabilidad **calibrada** |
| **Métrica de decisión** | Conversiones capturadas en el top-K (K = 20 %) |
| **Métrica de optimización** | PR-AUC y log-loss, no *accuracy*: el objetivo está desbalanceado (~15 %) |

El eslabón «fracción convertida × ticket medio» es un **supuesto**, declarado en
`conversion-sesion-problem`: el dataset no trae tarifa.

### El dataset

**Airlines Seat Booking** · [`anandshaw2001/airlines-booking-csv`](https://www.kaggle.com/datasets/anandshaw2001/airlines-booking-csv)
· 14 columnas · **CC0**. Cada fila es una **sesión de reserva** de British Airways.

| | |
|---|---|
| Filas en bronze | 50.000, sin nulos, **719 duplicadas exactas** |
| Tras la limpieza (silver) | 49.281 |
| Positivos (`booking_complete`) | 15,0 % |
| Split | 80/20 estratificado, semilla 42: train 39.424 · test 9.857 |

Segmentos con señal clara: `sales_channel` (Internet convierte ~15,5 %, Mobile ~10,8 %) y `trip_type`
(RoundTrip ~15 %, OneWay ~5 %). Detalle y figuras en `results/02-data_understanding/`.

### La comprobación que decidía la viabilidad: resuelta

> **¿Qué significa `wants_extra_baggage = 0` en una sesión que no se completó?**

Las tres banderas `wants_*` **no son fuga**: valen 1 también en sesiones no convertidas (equipaje
65 % frente a 75 % en las convertidas), o sea, se seleccionan durante la sesión. Se conservan como
features. Es una inferencia desde los datos, no una definición del sistema fuente: hay que
reconfirmarla con quien sea dueño del dato antes de servir
([`wants_leakage.md`](results/02-data_understanding/wants_leakage.md)).

### Lo que estas variables no permiten

- **No hay importe ni tarifa.** El ingreso depende de un ticket medio supuesto.
- **No hay identificador de cliente ni de sesión.** El split es por fila; sesiones del mismo cliente
  pueden caer a ambos lados y las cifras son una cota optimista.
- **No hay intervención observada.** Se modela *quién convierte*, no *a quién convertiría la
  intervención* (eso es uplift).
- **No hay fecha absoluta.** No hay split temporal limpio; `leakage-check` detecta columnas
  demasiado predictivas o prohibidas, no fugas temporales sutiles.

---

## Resultados

Candidato (gradient boosting calibrado) frente a la línea base (regresión logística), en **test**,
evaluado una sola vez y después de sellar el candidato:

| Métrica | Línea base | Candidato |
|---|---|---|
| PR-AUC | 0,348 | **0,371** |
| Conversiones capturadas en el top 20 % | 47,8 % | **49,9 %** |
| ECE (calibración) | 0,021 | **0,006** |

Cumple los umbrales de la spec, global y por segmento. Un segmento retrocede frente a la línea base
(`purchase_lead_bucket = 0-7`, −0,010 de PR-AUC) dentro de la tolerancia de 0,02, y se reporta.
Informe con figuras: [`results/05-evaluation/evaluacion.md`](results/05-evaluation/evaluacion.md).

Servido en local: latencia por sesión p99 ≈ 130–190 ms (presupuesto 250 ms); la regla de alertas de
drift da **1 % de falsos positivos** y **97,5 % de detección** sobre un desvío inyectado.

---

## Cómo se trabaja aquí

Cada unidad de trabajo es un **change de OpenSpec** y recorre el ciclo con los comandos `opsx`
(sus skills viven en `.claude/skills/openspec-*`):

```
/opsx:explore → /opsx:propose → /opsx:apply → /opsx:verify → /opsx:archive
                (proposal, specs,  (implementar    (coherencia +   (fusiona deltas
                 design, tasks)     y sellar)       gates)          y cierra)
```

`/opsx:verify` comprueba el change contra sus artefactos y, con la capa ML, corre los gates del alcance.
`/opsx:sync` fusiona los deltas a las main specs sin archivar. Cada paso tiene un subagente (`opsx-*`, en
`.claude/agents/`) y un orquestador que enruta. Los documentos bajo `openspec/` se
escriben en **español**; las palabras clave que el CLI interpreta (`### Requirement:`, `SHALL`,
`WHEN`, `THEN`, `## ADDED Requirements`) se mantienen tal cual.

### Los changes de este repositorio

| Change | Fases | Qué entregó |
|---|---|---|
| `conversion-sesion-data-foundation` | 01–03 | Problema definido, perfil de datos, veredicto sobre `wants_*`, silver validado; gates `data-contract` y `leakage-check` |
| `conversion-sesion-split-and-pipeline` | 03 | Split **antes** del feature engineering, feature store en `data/silver/`, pipeline de preprocesamiento como módulo propio, gate `train-serve-parity` |
| `conversion-sesion-modeling-evaluation` | 04–05 | Línea base y candidato en MLflow, sellado, evaluación por segmento y calibración, gates `slice-eval`, `behavioral-tests`, `incumbent-rerun` |
| `conversion-sesion-deploy-monitoring` | 06–07 | Registro y promoción con comprobante, función de despliegue, dashboard de monitoreo, gates de serving y monitoring |

Los cuatro están en `openspec/changes/archive/` con su evidencia.

### Del ciclo de vida a los artefactos

| Fase | Código | Salidas |
|---|---|---|
| 01 Negocio | `code/01-business_understanding/` | `results/01-business_understanding/problem.md` |
| 02 Datos | `code/02-data_understanding/` | `results/02-data_understanding/` (perfil, fuga de `wants_*`) |
| 03 Preparación | `code/03-data_preparation/` | feature store en `data/silver/`, `results/03-data_preparation/` |
| 04 Modelado | `code/04-modeling/` | runs y modelo registrado en MLflow, sello, `results/04-modeling/` |
| 05 Evaluación | `code/05-evaluation/` | `results/05-evaluation/` |
| 06 Despliegue | `code/06-deploy/` | inferencias en `data/gold/inferences/`, `results/06-deploy/` |
| 07 Monitoreo | `code/07_operation_and_monitoring/` | `results/07_operation_and_monitoring/dashboard.html` |

---

## El Spec Pack

Las capabilities de `conversion-sesion` viven en `openspec/specs/`:

| Capability | Gobierna |
|---|---|
| `conversion-sesion-problem` | Objetivos de negocio y de ML, ticket medio supuesto, no-objetivos |
| `conversion-sesion-data` | Esquema, rangos, feature store, split, `gold` reservada a inferencia |
| `conversion-sesion-features` | Feature engineering después del split, ajustado solo con train, pipeline reproducible |
| `conversion-sesion-evaluation` | Regla top-K, umbrales por segmento relativos a la línea base, calibración, comportamiento |
| `conversion-sesion-serving` | Versión registrada parametrizable, contrato E/S, registro de inferencias, latencia, rollback, promoción |
| `conversion-sesion-monitoring` | Drift (PSI), métricas de producto, umbrales y acciones, dashboard |

`training` y `governance` **no se especifican**: el modelo es Tier 2 y ese tier no los incluye
(`openspec/config.yaml`). Las exigencias de entrenamiento (MLflow, semilla, sellado) viven en el
diseño y en los gates de evaluación. Es la proporcionalidad del marco, no un olvido.

### Gates

Cada gate es un ejecutable en `gates/`: entra por CLI (`--change <id>`), sale con código 0 (pasa) o
distinto de 0 (bloquea) y un JSON en stdout. Leen su criterio del bloque `yaml contract` de la spec,
nunca lo llevan escrito dentro, y **recalculan** desde los artefactos en vez de fiarse de un archivo
de resultados.

| Aspecto | Gates implementados |
|---|---|
| `data` | `data-contract` (`freshness` es `non_binding`: no hay fecha) |
| `features` | `leakage-check`, `train-serve-parity` |
| `evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` |
| `serving` | `contract-compat`, `latency-p99`, `rollback-drill` |
| `monitoring` | `alert-backtest`, `false-positive-budget` |
| `problem` | `human-review`: evidencia manual (`human-review.json`), sin ejecutable |

Además: `seal.py` (congela candidato) y `receipt.py` (comprobante de promoción). Cada gate tiene un
test que demuestra que **puede fallar**: un gate que no puede fallar no es un gate.

---

## Reglas que el entorno impone

1. **Ninguna feature edita `openspec/specs/` directamente.** Se escribe un delta y la fusión ocurre
   al archivar. El hook `spec_pack_guard.py` bloquea la escritura directa con las herramientas de
   edición; `openspec archive` (por shell) es el camino legítimo.
2. **El candidato se sella antes de evaluarlo.** `gates/seal.py` congela cinco identidades (spec pack,
   dataset, código, entorno, modelo) más el `run_id` y **se niega a sobrescribir** un sello existente.
   `slice-eval` rechaza evaluar un modelo cuyo hash no coincida con el sello.
3. **El split va antes del feature engineering.** Escalado y target encoding se ajustan solo con
   train; test no participa.
4. **Cada paso tiene su precondición.** `sdd_phase_guard.py` bloquea despachar `opsx-verify` sin sello si
   el delta toca `evaluation`, y `opsx-archive` sin comprobante si toca `serving`.
5. **`champion` solo se asigna con comprobante.** `promote.py` exige un `receipt.json` que ligue las
   cinco identidades y los gates en verde; rollback = promover la versión anterior.
6. **Los gates se derivan del aspecto** de las capabilities que toca el delta, no de la fase.

---

## Despliegue y monitoreo (simulados)

No hay nube: el «despliegue» es una función con comando y el «monitoreo» un dashboard HTML.

```bash
python code/06-deploy/register_model.py             # v1 = línea base (rollback), v2 = candidato sellado
python code/06-deploy/promote.py --version 2        # champion, con comprobante
python code/06-deploy/predict.py                    # 3 sesiones al azar, alias champion
python code/06-deploy/predict.py --model-version 1  # otra versión: parámetro, no código
python code/06-deploy/simulate_traffic.py --batches 300 --drift-from-batch 220 --reset
python code/07_operation_and_monitoring/build_dashboard.py
```

- El modelo servido es una **versión registrada** de MLflow; cada inferencia guarda su versión y
  `run_id`, la probabilidad, la decisión, la latencia, el estado y **las entradas** (`in_*`), que
  son la base del data drift.
- El tráfico simulado se marca `source = simulation` y el dashboard lo rotula.
- El dashboard es un **HTML autocontenido, sin red**, con la marca y modo claro/oscuro: drift (PSI)
  por feature y en el tiempo, latencia, rechazo, categorías no vistas, tasa de intervención frente a
  K y segmentos. Un HTML abierto desde `file://` no puede leer Parquet, así que la «conexión» con
  Gold es el paso de construcción; se refresca volviendo a ejecutarlo.
- `mlflow.db` y `mlartifacts/` **no se versionan**: un clon limpio debe reejecutar 04 y el registro.

---

## Estructura

```
openspec/          config.yaml, main specs (Spec Pack) y changes (archive/ = cerrados)
code/<fase>/       scripts .py, una subcarpeta por fase; se ejecutan desde la raíz
data/bronze/       crudo, inmutable
data/silver/       feature store: limpio, train/test (crudos y transformados), pipeline, manifiesto
data/gold/         solo inferencia: data/gold/inferences/
results/<fase>/    markdown y tablas; las figuras van en results/<fase>/imgs/
gates/             los contratos, ejecutables, con sus tests
design_system/     avianca_brand — paquete de marca (pip -e)
.claude/           comandos opsx, skills openspec-*, subagentes opsx-* y hooks
```

Detalle de cada carpeta y sus reglas: [`CLAUDE.md`](CLAUDE.md#estructura).

---

## Políticas

- **Solo `.py`.** Nada de notebooks en el flujo gobernado: guardan estado oculto y orden de
  ejecución arbitrario, lo que rompe el sellado del candidato de raíz.
- **MLflow obligatorio**, con `signature` y flavor explícito. Sin signature, el esquema de
  `conversion-sesion-serving` no tiene con qué contrastarse y `contract-compat` dejaría de poder
  fallar.
- **Métricas por segmento**, no solo agregadas.
- **Todo análisis y toda decisión llevan una figura** en `results/<fase>/imgs/`, con el sistema de
  marca (`avianca_brand.apply_avianca_style()`; `create_dashboard` para figuras multi-panel y
  `slice_chart` para comparar candidato contra línea base por segmento).

El detalle está en [`CLAUDE.md`](CLAUDE.md#políticas-del-repositorio).

---

## Estado y límites

Completo: las siete fases de la demo, 6 capabilities, 11 gates de dominio ejecutables (más `seal` y `receipt`) y 4 changes archivados.

- **Los tres primeros changes se fusionaron sin comprobante**; solo `conversion-sesion-deploy-monitoring`
  tiene `receipt.json`. Falta emitir uno retroactivo para el candidato evaluado antes.
- **Sin resultados de conversión en línea**: se monitorean entradas, salidas y operación, no el
  desempeño del modelo servido.
- **Split por fila y sin fecha**: las métricas de test son una cota optimista.
- **Latencia y drift medidos en local** sobre tráfico simulado; no son compromisos de producción.
- Los subagentes `opsx-*` y sus precondiciones (`sdd_phase_guard.py`) están definidos y probados con
  tests, pero los changes de esta demo se trabajaron con los comandos `opsx` directamente.

---

## Licencia

Código de demostración. El dataset es CC0 (dominio público). Las marcas y los design tokens de
Avianca pertenecen a sus titulares y se usan aquí únicamente con fines de demostración.
