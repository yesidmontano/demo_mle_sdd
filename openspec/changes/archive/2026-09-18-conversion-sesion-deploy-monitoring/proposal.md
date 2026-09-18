## Why

El candidato de `conversion-sesion` pasó la evaluación, pero solo existe como un run de MLflow local: no hay forma controlada de usarlo sobre sesiones nuevas, ni de saber después si sigue comportándose. Este change cubre despliegue (06) y monitoreo (07), **simulados en local**: no hay nube; el «despliegue» es una función con comando de ejecución y el «monitoreo» es un dashboard HTML que lee lo que esa función deja en `data/gold/`.

## What Changes

- **Registro y promoción (06)**: el candidato sellado y la línea base se registran en el Model Registry de MLflow como versiones de `conversion-sesion` (v1 = línea base, destino de rollback; v2 = candidato). El alias `champion` solo se asigna con un **comprobante** (`receipt.json`) que liga spec pack, dataset, código, entorno, modelo y `run_id`.
- **Función de despliegue con comando** (`code/06-deploy/predict.py`): toma 2–3 sesiones al azar del dataset crudo, ejecuta el pipeline completo con la versión de modelo elegida y guarda las inferencias en `data/gold/inferences/`.
  - **Versión parametrizable**: `--model-version N` o `--model-alias champion` (por defecto). Cambiar de modelo es cambiar un parámetro, no código.
  - Cada inferencia guarda: id, lote, hora, **versión y `run_id` del modelo**, probabilidad, decisión de intervenir, latencia, **las entradas** (base para medir data drift) y estado (`ok`/`rejected`).
- **Regla de decisión en serving**: el top-K del ranking se traduce a un umbral de probabilidad calculado al registrar el modelo (cuantil 80 % de las puntuaciones de test) y guardado como etiqueta de la versión.
- **Simulador de tráfico** (`simulate_traffic.py`): ejecuta muchos lotes pequeños con la misma función, con horas repartidas en varios días y, opcionalmente, un desvío de datos inyectado, para que el dashboard tenga algo que mostrar. Las filas simuladas se marcan `source = simulation`.
- **Monitoreo (07)**: un dashboard HTML autocontenido (sin red, con la marca) generado desde `data/gold/inferences/`:
  - **data drift** (PSI por feature y de la puntuación contra el conjunto de entrenamiento),
  - **métricas de producto**: volumen, latencia p50/p95/p99, tasa de rechazo, categorías no vistas, tasa de intervención frente al K esperado, versión servida,
  - **segmentos** (canal, tipo de viaje, tramo de antelación), como exige la spec de evaluation.
  Cada señal con ventana, umbral, severidad y acción.
- **Gates**: `contract-compat`, `latency-p99` y `rollback-drill` (serving); `alert-backtest` y `false-positive-budget` (monitoring); más `gates/receipt.py`.
- **Límite declarado**: no hay resultados reales de conversión en línea, así que no se monitorea desempeño del modelo, solo entradas, salidas y operación.
- **Alternativa descartada**: un servicio HTTP (FastAPI) local. Añade proceso y puerto sin aportar a la demo; una función con comando cubre el contrato y se puede envolver en un servicio más adelante.

## Capabilities

### New Capabilities
- `conversion-sesion-serving`: modelo servido = versión registrada elegida y parametrizable, contrato de entrada/salida, registro de inferencias en Gold, latencia, rollback y promoción con comprobante.
- `conversion-sesion-monitoring`: señales de drift y de producto con ventana, umbral, severidad y acción; backtest de alertas y presupuesto de falsos positivos; dashboard.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código nuevo: `code/06-deploy/` (`register_model.py`, `promote.py`, `predict.py`, `simulate_traffic.py`), `code/07_operation_and_monitoring/` (`drift.py`, `build_dashboard.py`).
- Datos: `data/gold/inferences/` (Parquet por lote, no versionado), `data/silver/monitoring_reference.json` (referencia de drift).
- Salidas: `results/06-deploy/`, `results/07_operation_and_monitoring/dashboard.html` y figuras en `imgs/`.
- Gates nuevos: los cinco anteriores más `gates/receipt.py`; sus tests.
- Depende del MLflow local de la fase 04 (`mlflow.db`, `mlartifacts/`), que no se versiona.
- Tier 2: aplican los aspectos serving y monitoring.
