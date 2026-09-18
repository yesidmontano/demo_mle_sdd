## Why

Las fases 01–03 dejaron el problema definido y un feature store reproducible (`data/silver/`), pero no hay ningún modelo ni criterio para decidir si es utilizable. Este change cubre modelado (04) y evaluación (05) de `conversion-sesion`: entrena una línea base y un candidato, y decide con evidencia por segmento si el candidato merece avanzar a despliegue.

## What Changes

- **Modelado (04)**: dos modelos sobre `train_features`, ambos registrados en MLflow con `signature` y flavor `sklearn`:
  - **línea base**: regresión logística.
  - **candidato**: gradient boosting (`HistGradientBoostingClassifier`) con calibración de probabilidades.
  Cada uno se registra como un pipeline completo (preprocesamiento + clasificador): la entrada del modelo son sesiones crudas, no features ya transformadas.
- **Sellado antes de evaluar**: al terminar el entrenamiento se congela el candidato (`evidence/seal.json`: spec pack, dataset, código, entorno, modelo y `run_id`) antes de mirar ninguna métrica de test.
- **Evaluación (05)**: sobre `test_features`, una sola vez: métricas globales y por segmento, calibración, conversiones capturadas en el top-K, y pruebas de comportamiento.
- **Regla de decisión como cláusula de spec**: se interviene sobre el top 20 % del ranking (K = 20 %, supuesto de presupuesto). Cambiarlo es un change nuevo, no un ajuste de código.
- **Umbrales relativos a la línea base**, fijados en la spec antes de ver resultados. Un resultado negativo (el candidato no supera a la línea base) es un desenlace válido y se archiva como hallazgo.
- **Alcance por tier**: Tier 2 no incluye el aspecto `training`, así que no se abre `conversion-sesion-training`. Las exigencias de MLflow, semilla y sellado viven en el diseño y en los gates de evaluación.
- No se despliega nada ni se define serving ni monitoreo.
- **Alternativa descartada**: elegir el modelo comparando en test varios candidatos. Contamina test y convierte la evaluación en selección. Se elige con validación cruzada sobre train y test se toca una vez.

## Capabilities

### New Capabilities
- `conversion-sesion-evaluation`: regla de decisión top-K, umbrales por segmento relativos a la línea base, calibración, pruebas de comportamiento y exigencia de que lo evaluado sea el candidato sellado y registrado en MLflow.

### Modified Capabilities
<!-- Ninguna: no cambian requisitos de problem, data ni features. -->

## Impact

- Código nuevo: `code/04-modeling/`, `code/05-evaluation/`.
- Salidas nuevas: `results/04-modeling/`, `results/05-evaluation/` (con `imgs/`), `mlflow.db` y `mlartifacts/` (no versionados).
- Gates nuevos: `slice-eval`, `behavioral-tests`, `incumbent-rerun`, más `gates/seal.py` (sellado).
- Dependencias: `mlflow` (ya declarado en `requirements.txt`, aún no instalado en `.venv`).
- Tier 2; lo consumirá un change posterior de serving/despliegue.
