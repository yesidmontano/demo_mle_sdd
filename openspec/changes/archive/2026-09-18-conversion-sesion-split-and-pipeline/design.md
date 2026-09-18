## Context

El change archivado `conversion-sesion-data-foundation` produjo `silver` y `gold` como un solo dataset y derivó features antes de dividir. Hay que reordenar el proceso y dejar los artefactos claros para entrenamiento, evaluación y, sobre todo, despliegue. Sigue siendo una demo: sin frameworks de feature store, solo carpetas y archivos versionables por hash.

## Goals / Non-Goals

**Goals:**
- Orden: limpieza → split → feature engineering ajustado solo con train.
- `data/silver/` como feature store con todos los estados del dataset y el pipeline.
- Pipeline definido en su propio módulo, reutilizable por serving.
- `gold` vacía, reservada a inferencia.

**Non-Goals:**
- Entrenar o evaluar modelos; selección de features.
- Un feature store real (Feast, etc.).
- Split temporal o por grupos: no hay fecha ni id de cliente.

## Decisions

1. **Split antes del feature engineering, siempre.** El escalado y el target encoding aprenden estadísticos; ajustarlos con todo el dataset filtra información de test. Alternativa: transformar todo y dividir después; descartada. Se reconsidera solo para transformaciones sin estado, y aun así viven en el pipeline por uniformidad.
2. **Split 80/20 estratificado, semilla 42**, sobre `sessions.parquet` (ya limpio y deduplicado, así que no hay filas idénticas a ambos lados). Sin id de sesión ni de cliente el split es por fila; queda declarado como límite.
3. **Dos versiones de cada conjunto**: `train/test` (limpios, con las columnas originales) y `train_features/test_features` (transformados). Los primeros son la entrada del pipeline en serving y para la paridad; los segundos, la entrada del modelo.
4. **Pipeline sklearn `ColumnTransformer`** con salida DataFrame: derivadas por fila (`FunctionTransformer`), `StandardScaler` sobre numéricas (con `log1p` en `purchase_lead` y `length_of_stay`), `OneHotEncoder` para categóricas de baja cardinalidad y `TargetEncoder` para `route` y `booking_origin`. Se ajusta con `fit_transform(train)`, que en el `TargetEncoder` usa validación cruzada interna, y solo `transform(test)`. Alternativa: pandas a mano; descartada porque no se puede guardar ni reaplicar de forma fiel.
5. **Definición separada de ejecución**: `preprocessing.py` solo define `build_pipeline()` y las constantes de columnas, sin E/S; `run_preparation.py` orquesta limpieza, split, ajuste, guardado y reporte. Serving importa el primero.
6. **Manifiesto** `manifest.json`: semilla, versión de sklearn, conteos, tasa de positivos por conjunto, columnas de entrada/salida y SHA-256 de cada artefacto. Es lo que permite comprobar en despliegue que se usa la misma versión.
7. **`gold` vacía** (solo `.gitkeep`); se elimina `data/gold/sessions.parquet`.
8. **Gates**: `data-contract` valida presencia de archivos, split y `gold` vacía; `leakage-check` corre sobre `train_features`; `train-serve-parity` recarga el pipeline y compara contra `test_features`.

## Risks / Trade-offs

- [Split por fila con posible dependencia entre sesiones del mismo cliente] → declarado como límite; revisar cuando exista un id.
- [Artefacto joblib atado a la versión de sklearn] → el manifiesto registra la versión y `requirements.txt` la fija.
- [TargetEncoder con validación cruzada interna hace que train_features no sea igual a `transform(train)`] → la paridad se verifica sobre test, que es la comparación relevante para serving.
- [Hashes de parquet pueden cambiar entre versiones de pyarrow] → la reproducibilidad se comprueba por contenido (`equals`), el hash es informativo.
