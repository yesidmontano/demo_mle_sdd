## 1. Entendimiento del negocio (fase 01)

- [x] 1.1 Escribir `results/01-business_understanding/problem.md` con objetivo de negocio, objetivo de ML, métrica de decisión, supuesto de ticket medio y no-objetivos; coincide con `conversion-sesion-problem`
- [x] 1.2 Añadir a `results/01-business_understanding/imgs/` un diagrama del embudo de decisión (sesiones -> ranking -> top-K intervenido -> conversión incremental) referenciado desde `problem.md`
- [x] 1.3 Registrar en `evidence/` la aprobación `human-review` del enunciado del problema

## 2. Entendimiento de datos (fase 02)

- [x] 2.1 Implementar `code/02-data_understanding/profile.py`: forma, dtypes, nulos, duplicados, balance de clases, rangos por columna; escribe `results/02-data_understanding/profile.md` con figuras en `imgs/` (balance de clases, distribuciones y rangos de las numéricas)
- [x] 2.2 En el mismo script, comparar `wants_*` entre sesiones convertidas y no convertidas y escribir el veredicto en `results/02-data_understanding/wants_leakage.md`, respaldado por una figura de tasa de `wants_*` por clase en `imgs/`
- [x] 2.3 Añadir una figura de conversión por segmento (canal, tipo de viaje, tramo de antelación) con `avianca_brand`; guardarla en `results/02-data_understanding/imgs/`

## 3. Preparación de datos (fase 03)

- [x] 3.1 Implementar `code/03-data_preparation/build_layers.py`: leer bronze (sin escribirlo nunca), limpiar y deduplicar a `data/silver/sessions.parquet`, registrar las filas eliminadas
- [x] 3.2 En el mismo script, derivar `purchase_lead_bucket`, `is_weekend_flight` y `extras_count` en `data/gold/sessions.parquet`
- [x] 3.3 Implementar `gates/data_contract.py` y `gates/leakage_check.py` (CLI, código de salida, JSON en stdout) que lean los contratos del delta spec
- [x] 3.4 Añadir tests pytest de ambos gates, incluido un caso en que cada gate falle
- [x] 3.5 Generar en `results/03-data_preparation/imgs/` una figura antes/después de la limpieza (filas eliminadas, distribución de `purchase_lead` y su bucket) que respalde la decisión de deduplicar
- [x] 3.6 Reconstruir silver y gold desde bronze dos veces y confirmar salida idéntica

## 4. Verificación

- [x] 4.1 Correr `data-contract` y `leakage-check`; guardar las salidas en `openspec/changes/conversion-sesion-data-foundation/evidence/`
