## Why

Ventas y CRM no pueden intervenir en todas las sesiones de reserva: recordatorios, descuentos y retargeting cuestan dinero y desgastan al cliente. Hoy no existe un ranking de qué sesiones merecen esa intervención, ni una base de datos gobernada desde la cual entrenarlo. Este change cubre las tres primeras fases del ciclo de vida (entendimiento del negocio, entendimiento de datos, preparación de datos) del modelo `conversion-sesion`, para que el modelado parta de un problema definido y de un dataset validado y reproducible.

## What Changes

- **Objetivo de negocio**: ingreso incremental por sesión intervenida, dentro de un presupuesto de intervención fijo.
- **Objetivo de ML**: `P(booking_complete | atributos de la sesión)`, una probabilidad calibrada que sirve para ordenar sesiones; el umbral de decisión se fija después en `conversion-sesion-evaluation`, no aquí.
- **No-objetivos**: sin modelado de uplift, sin tarifa ni ingreso por sesión, sin historial de cliente, sin serving ni monitoreo (changes posteriores).
- **Enfoque**: perfilar `data/bronze/customer_booking.csv` (50.000 filas, ~15 % de positivos), verificar si las banderas `wants_*` filtran el objetivo, construir `silver` (limpio, tipado, sin duplicados) y `gold` (features listas para modelar + objetivo) con un script reproducible, y hacer cumplir el contrato de datos con un gate.
- **Alternativa descartada**: una heurística de reglas (p. ej. «intervenir cuando `purchase_lead` es corto»). No produce una probabilidad calibrada ni garantías por segmento, así que no sirve para un ranking con presupuesto; se reconsidera solo si el modelo no supera a la heurística en el top-K.
- En este change no se entrena ningún modelo ni se despliega nada.

## Capabilities

### New Capabilities
- `conversion-sesion-problem`: objetivo de negocio frente a objetivo de ML, ticket medio supuesto, métrica de decisión, no-objetivos.
- `conversion-sesion-data`: esquema, rangos, unicidad y linaje de `bronze`/`silver`/`gold`, más la aserción sobre la semántica de `wants_*`.
- `conversion-sesion-features`: conjunto de features de gold, qué banderas se admiten y reglas contra la fuga del objetivo.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ aún no contiene capabilities de este modelo. -->

## Impact

- Código nuevo: `code/01-business_understanding/`, `code/02-data_understanding/`, `code/03-data_preparation/`.
- Salidas nuevas: `results/02-data_understanding/` (perfil, verificación de fuga), `data/silver/`, `data/gold/`.
- Gates nuevos: `gates/data_contract.py` (data), `gates/leakage_check.py` (features); `human-review` para problem.
- Tier 2 (va a producción, impacto acotado y reversible), así que aplica el ciclo completo a los aspectos tocados: problem, data, features.
