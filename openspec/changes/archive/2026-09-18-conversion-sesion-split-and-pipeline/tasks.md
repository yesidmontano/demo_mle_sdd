## 1. Pipeline de preprocesamiento

- [x] 1.1 Crear `code/03-data_preparation/preprocessing.py` con `build_pipeline()` y las listas de columnas, sin E/S
- [x] 1.2 Crear `code/03-data_preparation/run_preparation.py`: limpieza a `data/silver/sessions.parquet`, split 80/20 estratificado (semilla 42) a `train.parquet`/`test.parquet`, ajuste del pipeline solo con train, `train_features`/`test_features`, `preprocessing_pipeline.joblib` y `manifest.json`
- [x] 1.3 Eliminar `code/03-data_preparation/build_layers.py` y `data/gold/sessions.parquet`; dejar `data/gold/` solo con `.gitkeep`
- [x] 1.4 Ejecutar el script y confirmar que corre dos veces con salida idéntica

## 2. Análisis visual y reporte

- [x] 2.1 Figura en `results/03-data_preparation/imgs/` del split (tamaño y tasa de positivos por conjunto) que respalde la estratificación
- [x] 2.2 Figura en `imgs/` de una variable antes y después de transformar (p. ej. `purchase_lead` crudo vs escalado) que respalde el pipeline
- [x] 2.3 Reescribir `results/03-data_preparation/preparacion.md` con el orden del proceso, el inventario del feature store y las figuras

## 3. Gates

- [x] 3.1 Actualizar `gates/data_contract.py` para `files_present`, métricas de split y `gold_data_files`
- [x] 3.2 Actualizar `gates/leakage_check.py` para leer train/test transformados y `split_overlap_rows`
- [x] 3.3 Crear `gates/train_serve_parity.py` (recarga el pipeline y compara contra `test_features`)
- [x] 3.4 Actualizar y ampliar los tests de gates, incluido un caso de fallo por cada gate nuevo

## 4. Documentación y verificación

- [x] 4.1 Actualizar en `CLAUDE.md` la tabla de carpetas de datos (silver = feature store, gold = inferencia)
- [x] 4.2 Correr los tres gates y guardar la salida en `evidence/`
