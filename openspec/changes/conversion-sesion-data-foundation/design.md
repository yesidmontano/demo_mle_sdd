## Context

Bronze es `data/bronze/customer_booking.csv`: 50.000 sesiones de reserva de British Airways, 14 columnas, sin nulos, ~15 % de `booking_complete`, 719 filas duplicadas exactas, sin id de sesión y sin fecha. Es una demo, así que el diseño prefiere un script pequeño por fase antes que un framework de pipelines. Aplica Tier 2; los gates de los aspectos tocados son `data-contract` (data), `leakage-check` (features) y `human-review` (problem).

## Goals / Non-Goals

**Goals:**
- Problema definido y revisado (fase 01).
- Perfil de datos y decisión sobre la fuga de `wants_*` registrados como hallazgos (fase 02).
- `bronze -> silver -> gold` reproducible, con gates de contrato (fase 03).

**Non-Goals:**
- Splits, encoders aprendidos de los datos, entrenamiento, evaluación, serving, monitoreo.
- Cualquier herramienta Spark/Airflow/dbt.

## Decisions

1. **Un script por fase, ejecutado desde la raíz del repo**: `code/02-data_understanding/profile.py` (perfil + verificación de fuga; escribe en `results/02-data_understanding/`) y `code/03-data_preparation/build_layers.py` (bronze -> silver -> gold). Alternativa: un notebook; descartada por política del repositorio (solo `.py`).
2. **Silver elimina las filas duplicadas exactas y registra el conteo.** Sin id de sesión no se distinguen de una sesión registrada dos veces; conservarlas dejaría un duplicado a ambos lados de un split posterior. Se reconsidera si aparece un id de sesión.
3. **Batch, sin estado.** Las capas se reconstruyen completas en cada corrida; no hay estado incremental que sellar.
4. **Gold solo tiene features por fila** (`purchase_lead_bucket`, `is_weekend_flight`, `extras_count`); el target/frequency encoding de `route` y `booking_origin` se difiere al modelado y se ajusta solo sobre el split de entrenamiento. Alternativa: codificar en gold; descartada porque aprende de todas las filas y filtra.
5. **`wants_*` se conserva solo si el perfil lo respalda.** Ya observado: entre sesiones no convertidas el 65 % tiene equipaje extra frente al 75 % de las convertidas, así que las no convertidas no son todo ceros, lo que apunta a selección durante la sesión. El script de perfil lo re-verifica y el resultado se escribe en los hallazgos.
6. **Los gates son CLIs pequeños** en `gates/` (código de salida 0/1, JSON en stdout) que leen las cotas del bloque `yaml contract`. Frescura y paridad train/serve son `non_binding` con la razón declarada.

## Risks / Trade-offs

- [La semántica de `wants_*` sigue siendo una inferencia desde los datos, no una definición del sistema fuente] → registrarla como supuesto en los hallazgos y reconfirmarla con la persona dueña del dato antes de servir.
- [Sin fecha no hay split temporal, y `leakage-check` solo detecta fuga a nivel de columna] → declarado en los no-objetivos del problema; revisar en modelado con un split agrupado.
- [Eliminar duplicados puede quitar sesiones repetidas genuinas] → el conteo se registra y lo acota el contrato `row_count >= 40000`.
- [Valores raros de `route`/`booking_origin`] → se resuelven en el modelado.
