# demo_mle_sdd — MLOps gobernado por especificaciones

> Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**: las especificaciones y los
> contratos gobiernan entrenamiento, validación, registro y promoción.
>
> Caso de uso: **conversión de reserva y revenue ancilar** sobre datos públicos de British Airways.

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
# 1. Entorno
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e design_system          # sistema de marca Avianca

# 2. Datos (requiere credenciales de Kaggle en ~/.kaggle/kaggle.json)
kaggle datasets download -d anandshaw2001/airlines-booking-csv -p data/bronze --unzip

# 3. Verificar que el andamiaje responde
openspec list --specs                 # capabilities del Spec Pack
python -c "import avianca_brand as ab; ab.apply_avianca_style(); print('marca ok')"
```

---

## El dataset

**Airlines Seat Booking** · [`anandshaw2001/airlines-booking-csv`](https://www.kaggle.com/datasets/anandshaw2001/airlines-booking-csv)
· 14 columnas · 3,15 MB · **CC0**

Cada fila es una **sesión de reserva** de British Airways. La variable objetivo es
`booking_complete`: si esa sesión terminó en una reserva confirmada.

> **Conteo de filas y tasa de positivos: sin verificar.** La ficha de Kaggle publica el tamaño del
> archivo y las columnas, no el número de registros ni el balance de clases. Ambos son
> precisamente el tipo de afirmación que debe vivir en `booking-conversion-data` como aserción
> comprobable, no en un README — de modo que el primer change del proyecto los mide y los declara,
> y `data-contract` falla si el archivo descargado no los cumple.

| Columna | Qué es |
|---|---|
| `num_passengers` | Pasajeros en la reserva |
| `sales_channel` | Internet o Mobile |
| `trip_type` | Round Trip · One Way · Circle Trip |
| `purchase_lead` | Días entre la reserva y el vuelo |
| `length_of_stay` | Días en destino |
| `flight_hour`, `flight_day` | Hora y día de salida |
| `route`, `booking_origin` | Ruta y país desde el que se reserva |
| `flight_duration` | Duración del vuelo, en horas |
| `wants_extra_baggage` | **Ancilar**: equipaje adicional |
| `wants_preferred_seat` | **Ancilar**: selección de asiento |
| `wants_in_flight_meals` | **Ancilar**: comida a bordo |
| `booking_complete` | **Objetivo**: la reserva se completó |

### Por qué este dataset para una demo de gobierno

Tres propiedades lo hacen útil, y ninguna es el tamaño:

1. **Las tres banderas `wants_*` son revenue ancilar**, que en una aerolínea es una parte real del
   ingreso y no un detalle. Eso convierte un problema de conversión en un problema de revenue sin
   forzar la analogía.
2. **El objetivo está desbalanceado.** Un desbalance marcado obliga a que los umbrales por
   segmento y la calibración sean necesarios de verdad, no decorativos — que es justamente lo que
   el marco pide en `booking-conversion-evaluation`. La proporción exacta la fija el primer
   change, no este documento.
3. **Los segmentos salen solos y son los que importan**: canal, tipo de viaje, tramo de antelación,
   origen de la reserva. `slice-eval` tiene con qué trabajar desde el primer día.

### Lo que este dataset NO permite

Conviene decirlo antes de que lo diga el evaluador:

- **No hay columna de fecha absoluta.** `purchase_lead` es relativo, así que un split temporal
  limpio no es posible. Se usa split estratificado por grupos, y eso **debilita el gate
  `leakage-check`**: puede detectar columnas prohibidas, no fugas temporales sutiles.
- **El objetivo no es dinero.** Es conversión. La cadena conversión → ingreso hay que argumentarla,
  y esa argumentación vive en `booking-conversion-problem`, no se da por supuesta.
- **Es un snapshot, no un flujo.** No hay deriva real que observar, así que la capability
  `booking-conversion-monitoring` se especifica y se contrasta contra incidentes simulados.

---

## El modelo

`booking-conversion` — predice `P(booking_complete)` para priorizar intervenciones sobre sesiones
con intención de compra y estimar el ingreso ancilar esperado.

Su Spec Pack son las capabilities que comparten prefijo en `openspec/specs/`:

| Capability | Gobierna |
|---|---|
| `booking-conversion-problem` | Objetivo de negocio vs objetivo de ML, métrica de decisión, no-objetivos |
| `booking-conversion-data` | Esquema, rangos, nulabilidad, cardinalidad de `route` y `booking_origin` |
| `booking-conversion-features` | Definición point-in-time, fuente offline/online, paridad train/serve |
| `booking-conversion-training` | Split, semilla, hiperparámetros, reproducibilidad |
| `booking-conversion-evaluation` | Umbrales **por segmento**, calibración, tests de comportamiento |
| `booking-conversion-serving` | Esquema E/S, p99, degradación, trazabilidad |
| `booking-conversion-monitoring` | Señales, ventanas, umbrales, severidad y acción |
| `booking-conversion-governance` | Tier de riesgo, aprobadores, retención, rollback |

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
  `booking-conversion-serving` no tiene con qué contrastarse y `contract-compat` deja de poder
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
| Spec Pack de `booking-conversion` | **Pendiente** |
| Gates de dominio | **Pendiente** — dependen del Spec Pack |
| Pipeline y modelo | **Pendiente** |

---

## Licencia

Código de demostración. El dataset es CC0 (dominio público). Las marcas y los design tokens de
Avianca pertenecen a sus titulares y se usan aquí únicamente con fines de demostración.
