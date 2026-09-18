## Why

La preparación de datos entregó un solo `sessions.parquet` en `gold` y derivó features sin haber hecho antes el split. Eso deja tres huecos: no hay datasets de entrenamiento y prueba para las fases siguientes, el pipeline de preprocesamiento no está definido como un artefacto propio y reproducible, y `gold` contiene datos que no le corresponden. Sin esto, el despliegue no puede repetir la misma transformación que vio el modelo al entrenar.

## What Changes

- **Orden del proceso**: limpieza y formateo → **split train/test** → feature engineering. El split va antes porque las transformaciones que aprenden de los datos (escalado, target encoding) se ajustan solo con train.
- **Feature store = `data/silver/`**: guarda el dataset limpio, `train.parquet` y `test.parquet` (crudos limpios, antes de transformar), `train_features.parquet` y `test_features.parquet` (ya transformados), el pipeline ajustado y un manifiesto con semilla, conteos y hashes.
- **Pipeline de preprocesamiento como módulo propio** (`code/03-data_preparation/preprocessing.py`), separado del script que lo ejecuta, para que serving lo importe tal cual. El pipeline ajustado se guarda como artefacto.
- **`gold` queda vacía**: reservada a datos de inferencia y pruebas de despliegue. **BREAKING**: se elimina `data/gold/sessions.parquet`.
- **Gates**: `leakage-check` pasa a leer los features de train; `train-serve-parity` deja de ser `non_binding` para el preprocesamiento (el pipeline guardado reproduce `test_features` desde los datos crudos de test).
- Split 80/20 estratificado por `booking_complete`, semilla fija. No hay id de cliente ni de sesión, así que el split es por fila; se declara como límite.
- **Alternativa descartada**: hacer feature engineering sobre todo el dataset y dividir después. Es más simple, pero el escalado y el target encoding verían las filas de test. Se reconsidera solo para transformaciones puramente por fila, que aquí ya viven dentro del pipeline por uniformidad.

## Capabilities

### New Capabilities
<!-- Ninguna. -->

### Modified Capabilities
- `conversion-sesion-data`: define qué guarda cada capa (silver como feature store, gold reservada a inferencia) y exige splits estratificados y sin solapamiento.
- `conversion-sesion-features`: el feature engineering ocurre después del split, se ajusta solo con train y se guarda como pipeline reproducible.

## Impact

- Código: `code/03-data_preparation/preprocessing.py` (nuevo), `code/03-data_preparation/run_preparation.py` (reemplaza a `build_layers.py`).
- Datos: `data/silver/{train,test,train_features,test_features}.parquet`, `data/silver/preprocessing_pipeline.joblib`, `data/silver/manifest.json`; se elimina `data/gold/sessions.parquet`.
- Gates: `gates/leakage_check.py` (lee train/test), `gates/train_serve_parity.py` (nuevo) y sus tests.
- `CLAUDE.md`: se actualiza la tabla de carpetas de datos.
- Fases 04 y 05 consumirán `train_features`/`test_features`.
