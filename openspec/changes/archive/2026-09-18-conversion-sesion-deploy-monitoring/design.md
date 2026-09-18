## Context

Existe el candidato sellado y evaluado (runs de MLflow en `mlflow.db`/`mlartifacts/`), el feature store en `data/silver/` y `data/gold/` vacía, reservada a inferencia. No hay nube: el despliegue y el monitoreo se simulan en local, pero con los mismos contratos que tendrían en producción (versión registrada, comprobante, entradas guardadas, alertas con umbral). Tier 2, así que aplican los aspectos serving y monitoring.

## Goals / Non-Goals

**Goals:**
- Un comando que sirva 2–3 sesiones con una versión de modelo parametrizable y guarde inferencias completas en `data/gold/inferences/`.
- Promoción con comprobante y rollback por parámetro.
- Dashboard HTML autocontenido con drift, métricas de producto y segmentos.
- Alertas probadas con un backtest, no solo dibujadas.

**Non-Goals:**
- API HTTP, contenedores, nube, autenticación.
- Monitoreo de desempeño real (no hay resultados de conversión en línea).
- Reentrenamiento automático; la acción de una alerta es abrir un change.

## Decisions

1. **Model Registry de MLflow**: se registra `conversion-sesion` con v1 = línea base (destino de rollback, sin alias `champion`) y v2 = candidato sellado. Cada versión lleva etiquetas: `run_id`, `role`, `k_fraction`, `decision_threshold`. Alternativa: apuntar al `run_id` directamente; descartada porque no da versión ni alias, que es lo que hace parametrizable el modelo.
2. **Comprobante mínimo** (`gates/receipt.py`): liga las cinco identidades del sello más el `run_id` y la versión registrada, y exige que los gates de evaluación (evidencia archivada) y los de serving estén en verde y que el hash del artefacto coincida. `promote.py --version N` solo asigna `champion` con comprobante válido, o a una versión marcada como destino de rollback. Sin esto, la promoción no sería un acto gobernado.
3. **Orden**: registrar v1 y v2 sin alias → correr los gates de serving contra `--model-version 2` → emitir comprobante → promover `champion`. Por eso los gates no dependen del alias.
4. **Carga con `mlflow.pyfunc`**, no con el flavor sklearn: así la `signature` se aplica al servir y una fila con esquema incorrecto se rechaza, que es lo que hace comprobable `contract-compat`. La salida es `predict_proba`; la probabilidad de conversión es la columna de la clase 1.
5. **Fuente de sesiones**: por defecto `data/bronze/customer_booking.csv` (crudo, sin el objetivo), parametrizable con `--source`. Las filas de bronze incluyen las usadas para entrenar; no importa porque no se evalúa desempeño con lo servido. Semilla parametrizable para repetir un lote.
6. **Registro de inferencias**: un Parquet por lote en `data/gold/inferences/`, una fila por sesión, con las entradas con prefijo `in_` (esquema estable para leer con un glob). No se versiona: son datos operativos. Los rechazos se guardan con `status = rejected` y motivo.
7. **Umbral de decisión**: `decision_threshold` = cuantil `1 - K` de las puntuaciones de test del candidato, calculado al registrar y guardado como etiqueta de la versión. K sale de la spec de evaluation. Alternativa: ranking por lote; descartada, un lote de 3 filas no tiene ranking significativo.
8. **Simulador de tráfico**: llama a la misma función `run_inference` en un bucle, con horas repartidas hacia atrás en el tiempo y un desvío opcional (`--drift-from-batch`) que sobremuestrea `sales_channel = Mobile`. Marca `source = simulation` en cada fila para que nunca se confunda con tráfico real.
9. **Referencia de drift**: `data/silver/monitoring_reference.json` con cortes de intervalos y frecuencias de train por feature, y los cortes y frecuencias de las puntuaciones de test del candidato. Se genera al registrar.
10. **PSI, un solo módulo** (`code/07_operation_and_monitoring/drift.py`) con la lógica de ventanas, severidad y señales, que usan el dashboard y los gates de alertas. Así el dashboard no puede discrepar del backtest.
11. **Backtest de alertas**: se sacan 200 ventanas de 200 filas de `train.parquet` sin desvío (mide falsos positivos) y otras 200 con el desvío inyectado (mide detección). Si el presupuesto falla, se ajusta la regla antes de sellar, no el umbral del gate.
12. **Dashboard**: el HTML se genera con un script que lee Gold, calcula todo en Python e incrusta los datos como JSON; el gráfico se dibuja con SVG y JS propios, sin librerías ni red. Un HTML abierto desde `file://` no puede leer Parquet ni hacer `fetch` a archivos locales, por eso la «conexión» con Gold es el paso de construcción (`build_dashboard.py`), que se vuelve a ejecutar para refrescar. Marca Avianca, con la skill de visualización de datos como guía.
13. **Latencia**: 200 inferencias de una fila con el modelo precalentado; se reporta también la carga del modelo (`model_load_ms`) como métrica de producto aparte.

## Risks / Trade-offs

- [PSI ruidoso con ventanas pequeñas y categorías raras] → ventana mínima de 200 y «otros» para categorías con menos de 1 %; el backtest mide el ruido real.
- [Un dashboard estático no es «en vivo»] → se declara; se refresca ejecutando el script. Si se quisiera vivo, bastaría servirlo con un proceso local.
- [Simulación puede confundirse con producción] → columna `source`, rótulo visible en el dashboard y nota en los resultados.
- [`mlflow.db` y `mlartifacts/` no se versionan] → un clon limpio debe reejecutar la fase 04 y el registro antes de servir; se documenta en `results/06-deploy/`.
- [Sin resultados reales no se ve degradación de desempeño] → límite declarado; el drift y la distribución de puntuaciones son la señal indirecta disponible.
- [Latencia local no es latencia en nube] → el umbral de 250 ms es una referencia de la demo, no un compromiso de producción.

## Migration Plan

1. Registrar v1 y v2. 2. Correr gates de serving y monitoring. 3. Emitir comprobante. 4. Promover `champion` a v2. Rollback: `python code/06-deploy/promote.py --version 1`. Lo servido no se pierde: cada inferencia lleva su versión.
