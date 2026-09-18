## Context

Existe un feature store en `data/silver/` (`train`/`test` limpios, `train_features`/`test_features` transformados, pipeline de preprocesamiento ajustado y manifiesto). No hay modelo previo en producción: la referencia contra la que comparar es una línea base simple. Sigue siendo una demo, así que se evita cualquier búsqueda de hiperparámetros o infraestructura extra. Tier 2: el aspecto `training` queda fuera del corte, y los gates de este change son los de `evaluation`.

## Goals / Non-Goals

**Goals:**
- Entrenar línea base y candidato con MLflow (signature y flavor), semilla fija y datos del feature store.
- Sellar el candidato antes de mirar test.
- Evaluar una sola vez sobre test, por segmento, con calibración y pruebas de comportamiento.
- Cada decisión con su figura, en `results/<fase>/imgs/`.

**Non-Goals:**
- Búsqueda de hiperparámetros, selección entre muchos modelos, XGBoost/LightGBM.
- Serving, latencia, monitoreo, comprobante de promoción.
- Uplift o ingreso por sesión (no-objetivos del problema).

## Decisions

1. **Línea base = regresión logística; candidato = `HistGradientBoostingClassifier` calibrado (sigmoide, 3 pliegues).** Hiperparámetros fijos y razonables, sin búsqueda. Alternativa: XGBoost, que `requirements.txt` declara; descartada para no depender de `libomp` ni de una instalación extra, y porque el gradient boosting de scikit-learn ya cubre el caso. Se reconsidera si el candidato no supera a la línea base.
2. **El modelo registrado es un `Pipeline` completo** (preprocesamiento ya ajustado + clasificador). La entrada es la sesión cruda (`INPUT_COLUMNS`), así que el modelo se despliega sin reconstruir el preprocesamiento. La `signature` se infiere sobre esas columnas; la salida es `predict_proba` (`pyfunc_predict_fn="predict_proba"`), y la probabilidad de conversión es la columna de la clase 1.
3. **Selección con validación cruzada sobre train, test se toca una vez.** 5 pliegues estratificados generan predicciones fuera de pliegue; sus métricas globales y por segmento se registran en el run de entrenamiento. Alternativa: comparar en test; descartada, contamina la evaluación.
4. **Sellado**: `gates/seal.py` congela cinco identidades (hash del Spec Pack, del dataset —según el manifiesto—, del código, del entorno y del artefacto del modelo) más el `run_id` y la hora, en `evidence/seal.json`. El script de entrenamiento lo invoca al terminar y antes de cualquier métrica de test. Alternativa: sellar a mano; descartada porque es lo que la regla «congelar antes de leer» busca evitar.
5. **Métricas**: PR-AUC y log-loss (optimización), ROC-AUC y Brier (contexto), ECE con 10 intervalos, y conversiones capturadas en el top-K. Se implementan una vez en `code/05-evaluation/metrics.py`, que usan el script y los gates.
6. **Los gates recalculan, no leen un JSON.** `slice-eval`, `behavioral-tests` e `incumbent-rerun` cargan el modelo desde MLflow por el `run_id` del sello y calculan sobre test. Un gate que confía en un archivo que él no produjo no puede fallar. K y los umbrales se leen del bloque `yaml contract` de la spec, no del código.
7. **Umbrales relativos a la línea base**, salvo la calibración (ECE ≤ 0,05), que es absoluta porque mide una propiedad de la probabilidad y no una mejora. Se fijan en la spec antes de evaluar.
8. **Segmentos**: canal de venta, tipo de viaje y tramo de antelación (`purchase_lead_bucket`), con al menos 500 sesiones. Se trasladarán a monitoreo cuando exista esa capability.
9. **MLflow**: seguimiento local en SQLite (`mlflow.db`) con artefactos en `mlartifacts/`, ninguno versionado (MLflow 3.16 ya no admite el file store `mlruns/`), experimento `conversion-sesion`, runs `conversion-sesion/<change_id>/<baseline|candidate>`. Se instala `mlflow` en `.venv` (ya está en `requirements.txt`).
10. **Resultado negativo**: si el candidato no cumple, el change no promueve y se archiva con `results/05-evaluation/hallazgo.md` y las figuras que lo muestran. Es un desenlace válido del marco.

## Risks / Trade-offs

- [`TargetEncoder` produce en train valores con validación cruzada y en inferencia el mapeo del train completo, una asimetría de scikit-learn] → se evalúa en test, que ya pasa por el camino de inferencia, y se declara en los hallazgos.
- [Split por fila sin id de cliente: sesiones del mismo cliente en ambos lados pueden inflar test] → límite ya declarado; leer las métricas como cota optimista.
- [Sin fecha no hay validación temporal] → sin cambio; se reconsidera con un origen de datos con fecha.
- [Umbrales por segmento con segmentos chicos son ruidosos] → mínimo de 500 sesiones por segmento.
- [`mlflow.db` y `mlartifacts/` no se versionan, así que el modelo no viaja en git] → el sello guarda `run_id` y hashes; reproducible reentrenando con el mismo código y semilla.
