## 1. Registro, comprobante y promoción (fase 06)

- [x] 1.1 Crear `code/06-deploy/register_model.py`: registrar la línea base (v1, destino de rollback) y el candidato sellado (v2) en el Model Registry, con etiquetas `run_id`, `role`, `k_fraction` y `decision_threshold`; escribir `data/silver/monitoring_reference.json`
- [x] 1.2 Crear `gates/receipt.py`: emitir `evidence/receipt.json` ligando las cinco identidades del sello, el `run_id` y la versión registrada, y verificar gates en verde y hash del modelo
- [x] 1.3 Crear `code/06-deploy/promote.py --version N`: asignar `champion` solo con comprobante válido, o a una versión destino de rollback

## 2. Función de despliegue

- [x] 2.1 Crear `code/06-deploy/predict.py`: `--model-version` o `--model-alias` (por defecto `champion`), `--n-rows` (por defecto 3), `--seed`, `--source`; carga por `mlflow.pyfunc`, ejecuta el pipeline completo y guarda el Parquet del lote en `data/gold/inferences/` con el esquema de la spec
- [x] 2.2 Rechazar filas inválidas con `status = rejected` y motivo sin detener el lote
- [x] 2.3 Crear `code/06-deploy/simulate_traffic.py`: muchos lotes con horas repartidas y desvío opcional, marcando `source = simulation`
- [x] 2.4 Escribir `results/06-deploy/despliegue.md` con el comando, los parámetros, el registro de versiones y la forma de hacer rollback; figura en `imgs/` con la latencia por sesión y su p99

## 3. Monitoreo (fase 07)

- [x] 3.1 Crear `code/07_operation_and_monitoring/drift.py`: PSI por feature y de puntuación, ventanas, severidades y señales de producto, usado por el dashboard y los gates
- [x] 3.2 Crear `code/07_operation_and_monitoring/build_dashboard.py`: leer `data/gold/inferences/` y generar `results/07_operation_and_monitoring/dashboard.html` autocontenido, con marca y sin URLs externas
- [x] 3.3 Figura en `results/07_operation_and_monitoring/imgs/` del backtest de alertas (PSI de ventanas sin y con desvío frente a los umbrales) y captura del dashboard; escribir `monitoreo.md`

## 4. Gates

- [x] 4.1 Crear `gates/contract_compat.py` (versión seleccionable, signature, fila inválida, columnas del registro, umbral y K, comprobante)
- [x] 4.2 Crear `gates/latency_p99.py` y `gates/rollback_drill.py`
- [x] 4.3 Crear `gates/alert_backtest.py` y `gates/false_positive_budget.py`
- [x] 4.4 Añadir tests de todos los gates nuevos, con un caso de fallo por cada uno

## 5. Cierre

- [x] 5.1 Registrar, correr los gates y emitir el comprobante; guardar la salida en `evidence/`
- [x] 5.2 Promover `champion` a v2, generar tráfico simulado (con y sin desvío) y construir el dashboard
- [x] 5.3 Actualizar `CLAUDE.md` con la convención de `data/gold/inferences/` y del comando de despliegue
