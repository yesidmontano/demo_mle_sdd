# demo_mle_sdd — MLOps gobernado por especificaciones

> Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**: las especificaciones y los
> contratos gobiernan entrenamiento, validación, registro y promoción.
>
> Caso de uso: **modelo conversión de sesión** sobre datos públicos de reservas de British
> Airways.

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

La explicación completa del marco está en [`CLAUDE.md`](CLAUDE.md).

---

## Quick path

```bash
# 1. Entorno — Python 3.12. El .venv es local y no se versiona; créalo si no lo tienes:
#    python3.12 -m venv .venv
source .venv/bin/activate
python --version                      # debe decir 3.12.x
pip install -r requirements.txt
pip install -e design_system          # sistema de marca Avianca

# 2. Datos (requiere credenciales de Kaggle en ~/.kaggle/kaggle.json)
kaggle datasets download -d anandshaw2001/airlines-booking-csv -p data/bronze --unzip

# 3. Verificar que el andamiaje responde
openspec list --specs                 # capabilities del Spec Pack
python -c "import avianca_brand as ab; ab.apply_avianca_style(); print('marca ok')"
```

---

## El problema analítico

**Modelo conversión de sesión** (`conversion-sesion`) — estima la probabilidad de que una sesión
de reserva termine en compra, para decidir **sobre qué sesiones intervenir**.

### La decisión de negocio

El presupuesto de intervención es finito: un recordatorio, un descuento o una campaña de
retargeting cuestan dinero y desgastan al cliente si se aplican a todo el mundo. La pregunta
operativa es a qué sesiones vale la pena dedicarlos.

El modelo produce un ranking; **la decisión la produce un umbral**. Y ese umbral es una cláusula
de `conversion-sesion-evaluation`, no una constante en el código: cambiarlo es un change con su
gate, no un ajuste silencioso. Esa es la demostración más limpia de lo que el marco hace.

### El objetivo de ML

Clasificación binaria sobre `booking_complete`, con **probabilidad calibrada** como salida — no
una etiqueta. Un ranking solo es útil si la probabilidad significa lo que dice.

| | |
|---|---|
| **Objetivo de negocio** | Ingreso incremental por sesión intervenida, dentro de un presupuesto fijo |
| **Objetivo de ML** | `P(booking_complete \| atributos de la sesión)` |
| **Métrica de decisión** | Conversiones capturadas en el top-K del ranking |
| **Métrica de optimización** | Log-loss o PR-AUC, no *accuracy* — el objetivo está desbalanceado |

La traducción entre ambos objetivos es explícita y hay que defenderla: el modelo ordena, la
intervención convierte una fracción de lo ordenado, y esa fracción por el ticket medio es el
ingreso. **Ese eslabón es un supuesto**, y vive declarado en `conversion-sesion-problem`.

### Por qué estos predictores deberían funcionar

Hay mecanismo detrás de cada uno, que es lo que hace defendible el modelo ante una pregunta
incómoda:

| Predictor | Mecanismo |
|---|---|
| `purchase_lead` | Reservar con mucha antelación señala planificación; a última hora, urgencia. Las dos convierten distinto |
| `sales_channel` | Móvil y web tienen fricción de checkout muy distinta |
| `num_passengers` | Reservas de grupo implican más coordinación y más abandono |
| `length_of_stay`, `trip_type` | Distinguen viaje de ocio de viaje de trabajo, con intención distinta |
| `booking_origin` | Mercado, poder adquisitivo y hábito de compra en línea |
| `flight_hour`, `flight_day` | Vuelo incómodo o en fin de semana cambia el perfil de quien reserva |
| `route`, `flight_duration` | Competencia en la ruta y peso de la decisión |

### La comprobación que decide la viabilidad

Hay una pregunta que el esquema no responde y que condiciona todo el Spec Pack:

> **¿Qué significa `wants_extra_baggage = 0` en una sesión que no se completó?**

- **Si las banderas registran lo que el cliente seleccionó durante la sesión**, aunque luego
  abandonara, son **predictores legítimos y probablemente fuertes**: quien ya eligió equipaje ha
  mostrado intención.
- **Si solo se rellenan al completar la reserva**, entonces valen 0 en toda sesión no convertida y
  son **fuga pura**. Un modelo que las use alcanzaría un desempeño casi perfecto en validación y
  sería inservible en producción, porque en el momento de decidir no se conocen.

Es el modo de falla más clásico del oficio y el más difícil de ver cuando las métricas salen
buenas. Se resuelve con una tabla cruzada de dos líneas.

Esa afirmación vive en `conversion-sesion-data` como aserción comprobable, y determina si las tres
banderas entran o no en el conjunto de features — decisión que se cierra en `sdd-design`.

### Lo que estas variables no permiten

Va en los no-objetivos del Spec Pack:

- **No hay importe ni tarifa.** El ingreso se estima con un ticket medio declarado como supuesto;
  el modelo no distingue una conversión cara de una barata.
- **No hay identificador de cliente.** Sin historial no hay features de comportamiento pasado, y
  tampoco se puede impedir que dos sesiones del mismo cliente caigan a lados distintos del split.
- **No hay intervención observada.** Se modela *quién convierte*, no *a quién convertiría la
  intervención*. Eso es uplift, y requiere asignación de tratamiento que este dataset no tiene.
- **No hay fecha absoluta.** `purchase_lead` es relativo, así que no hay split temporal limpio.
  Eso **debilita `leakage-check`**: detecta columnas prohibidas, no fugas temporales sutiles.
- **`route` y `booking_origin` tienen cardinalidad alta.** Un target encoding mal hecho es fuga, y
  eso es materia de `conversion-sesion-features`.

### Una decisión de diseño anticipada

¿Entran las tres banderas `wants_*` en el conjunto de features? Depende por completo de la
comprobación anterior, y la respuesta cambia el modelo entero. Se decide en `sdd-design` y se
declara en `conversion-sesion-features`, con su fuente offline y online — porque una feature que
en producción no está disponible en el momento de predecir es el train/serve skew de manual.

---

## El dataset

**Airlines Seat Booking** · [`anandshaw2001/airlines-booking-csv`](https://www.kaggle.com/datasets/anandshaw2001/airlines-booking-csv)
· 14 columnas · 3,15 MB · **CC0**

Cada fila es una **sesión de reserva** de British Airways.

> **Conteo de filas y balance de clases: sin verificar.** La ficha de Kaggle publica el tamaño del
> archivo y las columnas, no el número de registros ni la proporción de conversiones. Ambos son
> precisamente el tipo de afirmación que debe vivir en `conversion-sesion-data` como aserción
> comprobable, no en un README.

| Columna | Papel | Qué es |
|---|---|---|
| `num_passengers` | predictor | Pasajeros en la reserva |
| `sales_channel` | predictor | Internet o Mobile |
| `trip_type` | predictor | Round Trip · One Way · Circle Trip |
| `purchase_lead` | predictor | Días entre la reserva y el vuelo |
| `length_of_stay` | predictor | Días en destino |
| `flight_hour`, `flight_day` | predictor | Hora y día de salida |
| `route`, `booking_origin` | predictor | Ruta y país desde el que se reserva |
| `flight_duration` | predictor | Duración del vuelo, en horas |
| `wants_extra_baggage` | **por decidir** | Equipaje adicional — ver la comprobación de viabilidad |
| `wants_preferred_seat` | **por decidir** | Selección de asiento — ídem |
| `wants_in_flight_meals` | **por decidir** | Comida a bordo — ídem |
| `booking_complete` | **objetivo** | La reserva se completó |

### Por qué este dataset para una demo de gobierno

1. **El desbalance obliga a calibrar.** Con una clase minoritaria marcada, la calibración y los
   umbrales por segmento dejan de ser adorno: sin ellos el ranking no significa nada. Es
   exactamente lo que `conversion-sesion-evaluation` exige.
2. **El umbral de decisión es una cláusula de spec.** Cambiar dónde se corta el ranking es un
   change con su gate, y se ve en dos minutos durante una sustentación.
3. **Trae su propia trampa de fuga.** Las tres banderas `wants_*` pueden ser el mejor predictor o
   veneno puro según lo que signifique un cero. Un marco que presume de gobernar datos tiene aquí
   un caso real que resolver, no uno inventado.
4. **Los segmentos salen solos**: canal, tipo de viaje, tramo de antelación y origen de la
   reserva. `slice-eval` tiene con qué trabajar desde el primer día.

---

## El modelo

`conversion-sesion`. Su Spec Pack son las capabilities que comparten prefijo en
`openspec/specs/`:

| Capability | Gobierna |
|---|---|
| `conversion-sesion-problem` | Objetivo de negocio vs objetivo de ML, ticket medio supuesto, no-objetivos |
| `conversion-sesion-data` | Esquema, rangos, cardinalidad, y la semántica de `wants_*` sin conversión |
| `conversion-sesion-features` | Si entran las banderas, encoding de alta cardinalidad, paridad train/serve |
| `conversion-sesion-training` | Split por grupos, semilla, hiperparámetros, reproducibilidad |
| `conversion-sesion-evaluation` | Umbral de decisión, calibración, umbrales **por segmento**, comportamiento |
| `conversion-sesion-serving` | Esquema E/S, p99, degradación, trazabilidad |
| `conversion-sesion-monitoring` | Señales, ventanas, umbrales, severidad y acción |
| `conversion-sesion-governance` | Tier de riesgo, aprobadores, retención, rollback |

---

## Estructura

```
openspec/          config, main specs (Spec Pack) y changes en vuelo
code/<fase>/       scripts .py, una subcarpeta por fase
data/              bronze (crudo, inmutable) · silver (validado) · gold (listo para entrenar)
results/<fase>/    markdown, PNG y tablas — lo que se lee
gates/             los contratos, ejecutables
design_system/     avianca_brand — paquete de marca (pip -e)
.claude/           agents · skills · hooks
```

Detalle de cada carpeta y sus reglas: [`CLAUDE.md`](CLAUDE.md#estructura).

---

## Cómo se trabaja aquí

Cada unidad de trabajo es un **change** y recorre el ciclo SDD completo, esté en la fase del ciclo
de vida que esté:

```
sdd-init → sdd-explore → sdd-propose → sdd-spec → sdd-design → sdd-tasks
         → sdd-apply → sdd-verify → sdd-archive
```

Tres reglas que el entorno impone, no la buena voluntad:

1. **Ninguna feature edita `openspec/specs/` directamente.** Se escribe un delta; la fusión ocurre
   al archivar, y solo con comprobante. Un hook lo bloquea.
2. **El candidato se sella antes de evaluarlo.** Congelar antes de leer: así la evidencia pertenece
   a la versión exacta que se promueve.
3. **El subagente que implementa no es el que aprueba.** `sdd-apply` y `sdd-verify` nunca comparten
   contexto.

Los gates que una feature debe pasar **se derivan del aspecto de las capabilities que toca su
delta**, no de la fase en que se sitúa. Esa es la regla que hace mecánico al marco.

---

## Políticas

- **Solo `.py`.** Nada de notebooks en el flujo gobernado: guardan estado oculto y orden de
  ejecución arbitrario, lo que rompe el sellado del candidato de raíz.
- **MLflow obligatorio**, con `signature` inferida y flavor explícito. Sin signature, el esquema de
  `conversion-sesion-serving` no tiene con qué contrastarse y `contract-compat` deja de poder
  fallar — deja de ser un gate.
- **Métricas por segmento**, no solo agregadas.
- **Toda figura usa el sistema de marca.** `avianca_brand.apply_avianca_style()` al inicio del
  script. Para comparar candidato contra línea base por segmento está `slice_chart`.

El detalle está en [`CLAUDE.md`](CLAUDE.md#políticas-del-repositorio).

---

## Estado

| Pieza | Estado |
|---|---|
| Marco, skills, agentes y hooks | Completo |
| Sistema de marca `avianca_brand` | Completo y probado |
| Spec Pack de `conversion-sesion` | **Pendiente** |
| Gates de dominio | **Pendiente** — dependen del Spec Pack |
| Pipeline y modelo | **Pendiente** |

---

## Licencia

Código de demostración. El dataset es CC0 (dominio público). Las marcas y los design tokens de
Avianca pertenecen a sus titulares y se usan aquí únicamente con fines de demostración.
