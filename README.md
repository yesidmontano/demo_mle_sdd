# demo_mle_sdd — MLOps gobernado por especificaciones

> Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**: las especificaciones y los
> contratos gobiernan entrenamiento, validación, registro y promoción.
>
> Caso de uso: **modelo upsell esperado** — ingresos complementarios sobre datos públicos de
> British Airways.

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

**Modelo upsell esperado** (`upsell-esperado`) — estima la propensión de una sesión de reserva a
contratar cada servicio adicional, para decidir **qué extra ofrecer, a quién y en qué momento**.

### La decisión de negocio

El espacio en el flujo de reserva es finito: no se pueden empujar los tres extras con la misma
prominencia sin degradar la experiencia y sin canibalizarse entre sí. La pregunta operativa es a
qué sesión mostrarle qué.

La métrica de decisión son los **ingresos complementarios esperados** por sesión:

```
upsell_esperado(sesión) = Σ  P(contrata extra_i | atributos de la sesión) × precio_i
                         i
```

El vector de precios **no está en el dataset**: es un supuesto declarado en
`upsell-esperado-problem`. Sin él, la métrica queda en *número esperado de extras*, que sigue
siendo ordenable y suficiente para priorizar.

### El objetivo de ML

Tres salidas binarias sobre los mismos 10 predictores:

`wants_extra_baggage` · `wants_preferred_seat` · `wants_in_flight_meals`

Lo que hace interesante a este objetivo para el marco: **el objetivo ya es ingreso.** Equipaje,
asiento y comida se facturan, así que no hay que argumentar ninguna cadena desde una métrica
proxy hasta el dinero — el eslabón más frágil de la mayoría de propuestas de ML.

### Por qué estos predictores deberían funcionar

No es correlación ciega; hay mecanismo detrás de cada uno, y eso es lo que hace defendible el
modelo ante una pregunta incómoda:

| Predictor | Mecanismo |
|---|---|
| `length_of_stay`, `trip_type` | Estancias largas y viajes de ida y vuelta piden **equipaje** |
| `flight_duration` | A más horas de vuelo, más probable la **comida a bordo** |
| `num_passengers` | Grupos y familias quieren **sentarse juntos** |
| `purchase_lead` | Antelación como señal de planificación y de sensibilidad al precio |
| `sales_channel` | Móvil y web tienen fricción distinta en el flujo de upsell |
| `booking_origin` | Norma cultural y poder adquisitivo por mercado |
| `flight_hour`, `flight_day` | Vuelo de madrugada o en fin de semana cambia el perfil de viaje |

Los diez predictores son atributos de la sesión **conocidos antes** de que el cliente elija los
extras, así que no hay fuga temporal obvia — el problema habitual con datos de reserva.

### La comprobación que decide la viabilidad

Hay una pregunta que el esquema no puede responder y que condiciona todo el Spec Pack:

> **¿Qué significa `wants_extra_baggage = 0` en una sesión que no se completó?**

- **Si las banderas registran lo que el cliente seleccionó durante la sesión**, aunque luego
  abandonara, el dato es válido y el modelo es directo.
- **Si solo se rellenan al completar la reserva**, todas las sesiones con `booking_complete = 0`
  llevan ceros por construcción. El modelo no aprendería propensión a extras: **aprendería a
  predecir la conversión**, con métricas excelentes y valor nulo.

Es una fuga catastrófica y silenciosa, y se detecta con una tabla cruzada de dos líneas. Si se da
el segundo caso, el modelo se condiciona a reservas completadas —menos muestra, sigue siendo
válido— y la decisión de negocio se desplaza: de *qué ofrecer durante la sesión* a *qué ofrecer
tras confirmar*.

Esta afirmación vive en `upsell-esperado-data` como aserción comprobable, no en este README. El
primer change la mide y la declara, y `data-contract` falla si el archivo no la cumple.

### Lo que estas variables no permiten

Está en los no-objetivos del Spec Pack, y conviene decirlo antes de que lo pregunten:

- **No hay importe ni precio.** El ingreso esperado sale en unidades de extras salvo que se
  declare el vector de precios como supuesto.
- **No hay identificador de cliente.** Sin historial no hay features de comportamiento pasado, y
  tampoco se puede impedir que dos sesiones del mismo cliente caigan a lados distintos del split.
- **No se sabe qué se ofreció ni a qué precio.** Se modela propensión *dado que se ofreció*; no
  hay forma de estimar elasticidad ni el efecto de la oferta.
- **No hay fecha absoluta.** `purchase_lead` es relativo, así que no hay split temporal limpio ni
  estacionalidad observable. Eso **debilita `leakage-check`**: detecta columnas prohibidas, no
  fugas temporales sutiles.
- **`route` y `booking_origin` tienen cardinalidad alta.** Cientos de rutas y decenas de países
  obligan a decidir el encoding con cuidado: un target encoding mal hecho es fuga, y eso es
  materia de `upsell-esperado-features`.

### Una decisión de diseño anticipada

¿Puede `wants_preferred_seat` ser predictor de `wants_extra_baggage`? Depende de si el upsell se
muestra **todo junto** —entonces no se conoce ninguno al predecir— o **en secuencia** —entonces sí
se conocen los anteriores—. Se resuelve en `sdd-design`, y determina la paridad train/serve: usar
como feature algo que en producción no está disponible es el train/serve skew de manual.

---

## El dataset

**Airlines Seat Booking** · [`anandshaw2001/airlines-booking-csv`](https://www.kaggle.com/datasets/anandshaw2001/airlines-booking-csv)
· 14 columnas · 3,15 MB · **CC0**

Cada fila es una **sesión de reserva** de British Airways.

> **Conteo de filas y balance de clases: sin verificar.** La ficha de Kaggle publica el tamaño del
> archivo y las columnas, no el número de registros ni la proporción de positivos de cada bandera.
> Ambos son precisamente el tipo de afirmación que debe vivir en `upsell-esperado-data` como
> aserción comprobable, no en un README.

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
| `wants_extra_baggage` | **objetivo** | Equipaje adicional |
| `wants_preferred_seat` | **objetivo** | Selección de asiento |
| `wants_in_flight_meals` | **objetivo** | Comida a bordo |
| `booking_complete` | condicionante | La reserva se completó — ver la comprobación de viabilidad |

### Por qué este dataset para una demo de gobierno

Tres propiedades, y ninguna es el tamaño:

1. **El objetivo es dinero.** Las tres banderas son ingresos complementarios facturables, así que
   la métrica de decisión no necesita una cadena de traducción desde un proxy.
2. **Tres salidas son tres contratos.** `upsell-esperado-evaluation` tiene que declarar umbrales
   por extra **y** por segmento, y responder a una pregunta que el marco resuelve bien: *¿bloquea
   el gate si empeora uno de los tres pero mejoran los otros dos?* La respuesta va en la spec, no
   en el criterio de quien mira las métricas.
3. **Los segmentos salen solos y son los que importan**: canal, tipo de viaje, tramo de antelación
   y origen de la reserva. `slice-eval` tiene con qué trabajar desde el primer día.

---

## El modelo

`upsell-esperado`. Su Spec Pack son las capabilities que comparten prefijo en `openspec/specs/`:

| Capability | Gobierna |
|---|---|
| `upsell-esperado-problem` | Objetivo de negocio vs objetivo de ML, vector de precios, no-objetivos |
| `upsell-esperado-data` | Esquema, rangos, cardinalidad, y la semántica de `wants_*` sin conversión |
| `upsell-esperado-features` | Encoding de alta cardinalidad, point-in-time, paridad train/serve |
| `upsell-esperado-training` | Split por grupos, semilla, hiperparámetros, reproducibilidad |
| `upsell-esperado-evaluation` | Umbrales **por extra y por segmento**, calibración, comportamiento |
| `upsell-esperado-serving` | Esquema E/S de tres salidas, p99, degradación, trazabilidad |
| `upsell-esperado-monitoring` | Señales, ventanas, umbrales, severidad y acción |
| `upsell-esperado-governance` | Tier de riesgo, aprobadores, retención, rollback |

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
sdd-init → sdd-explore → sdd-spec → sdd-design → sdd-tasks → sdd-apply → sdd-verify → sdd-archive
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
  `upsell-esperado-serving` no tiene con qué contrastarse y `contract-compat` deja de poder
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
| Spec Pack de `upsell-esperado` | **Pendiente** |
| Gates de dominio | **Pendiente** — dependen del Spec Pack |
| Pipeline y modelo | **Pendiente** |

---

## Licencia

Código de demostración. El dataset es CC0 (dominio público). Las marcas y los design tokens de
Avianca pertenecen a sus titulares y se usan aquí únicamente con fines de demostración.
