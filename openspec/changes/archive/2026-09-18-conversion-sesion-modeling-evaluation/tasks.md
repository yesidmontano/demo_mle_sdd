## 1. Preparación

- [x] 1.1 Instalar `mlflow` en `.venv` y comprobar que `python -c "import mlflow"` funciona
- [x] 1.2 Crear `code/05-evaluation/metrics.py` (PR-AUC, log-loss, ROC-AUC, Brier, ECE, capturadas en top-K, métricas por segmento) con tests en `gates/tests/`

## 2. Modelado (fase 04)

- [x] 2.1 Crear `code/04-modeling/train.py`: entrena línea base y candidato sobre `train_features`, semilla fija, y los registra en MLflow como pipeline completo con `signature`, `input_example` y flavor `sklearn`
- [x] 2.2 En el mismo script, calcular predicciones fuera de pliegue (5 pliegues estratificados) y registrar métricas globales y por segmento de validación en cada run
- [x] 2.3 Crear `gates/seal.py` y sellar el candidato al terminar el entrenamiento, antes de cualquier métrica de test; produce `evidence/seal.json`
- [x] 2.4 Generar en `results/04-modeling/imgs/` la comparación de validación entre línea base y candidato (global y por segmento) y la curva de calibración fuera de pliegue; escribir `results/04-modeling/modelado.md`

## 3. Evaluación (fase 05)

- [x] 3.1 Crear `code/05-evaluation/evaluate.py`: cargar los modelos por el `run_id` del sello, evaluar una sola vez sobre `test_features`, con K leído de la spec, y registrar las métricas en MLflow
- [x] 3.2 Generar en `results/05-evaluation/imgs/` el gráfico por segmento (`slice_chart`), la curva de ganancia acumulada con K marcado y la curva de calibración de test
- [x] 3.3 Escribir `results/05-evaluation/evaluacion.md` con la decisión y las figuras que la respaldan

## 4. Gates

- [x] 4.1 Crear `gates/slice_eval.py` (sello, umbrales relativos a la línea base, por segmento, calibración)
- [x] 4.2 Crear `gates/behavioral_tests.py` (probabilidades válidas, categoría no vista, dirección de `wants_*`)
- [x] 4.3 Crear `gates/incumbent_rerun.py` (reentrena la línea base y compara log-loss)
- [x] 4.4 Añadir tests de los tres gates, incluido un caso de fallo por cada uno

## 5. Cierre

- [x] 5.1 Correr los tres gates y guardar la salida en `evidence/`
- [x] 5.2 Si algún gate falla, escribir `results/05-evaluation/hallazgo.md` con el resultado negativo y no promover
