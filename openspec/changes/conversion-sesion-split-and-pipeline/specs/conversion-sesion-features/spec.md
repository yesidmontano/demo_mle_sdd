## ADDED Requirements

### Requirement: El feature engineering ocurre después del split y se ajusta solo con train

El pipeline de preprocesamiento SHALL ajustarse únicamente con `train.parquet` y SHALL aplicarse a `test.parquet` sin reajustarse. Solo conocen features disponibles mientras la sesión sigue abierta; las banderas `wants_*` se conservan según la exploración de la fase 02.

#### Scenario: Test no influye en el pipeline

- **WHEN** se ajusta el pipeline
- **THEN** ninguna fila de test participa en el ajuste, y el gate de fuga no encuentra features con AUC individual sospechoso ni columnas prohibidas

```yaml contract
gate: leakage-check
train: data/silver/train_features.parquet
test: data/silver/test_features.parquet
assert:
  - metric: single_feature_auc
    op: "<"
    value: 0.85
    applies_to: all_features
  - metric: forbidden_columns_present
    op: "=="
    value: 0
    forbidden: [booking_complete_copy]
  - metric: split_overlap_rows
    op: "=="
    value: 0
```

### Requirement: El pipeline de preprocesamiento es un artefacto reproducible

El pipeline SHALL definirse en un módulo propio (`code/03-data_preparation/preprocessing.py`), guardarse ajustado en `data/silver/preprocessing_pipeline.joblib` y registrar en el manifiesto las columnas de entrada y de salida. Las transformaciones SHALL incluir las derivadas por fila (`purchase_lead_bucket`, `is_weekend_flight`, `extras_count`), escalado de numéricas, one-hot de categóricas de baja cardinalidad y target encoding de `route` y `booking_origin`.

#### Scenario: Paridad entrenamiento/serving del preprocesamiento

- **WHEN** se carga el pipeline guardado y se aplica a `test.parquet`
- **THEN** el resultado coincide con `test_features.parquet`

```yaml contract
gate: train-serve-parity
pipeline: data/silver/preprocessing_pipeline.joblib
raw: data/silver/test.parquet
transformed: data/silver/test_features.parquet
assert:
  - metric: max_abs_diff
    op: "<="
    value: 1.0e-9
```

## REMOVED Requirements

### Requirement: Gold solo contiene features conocidas al predecir
**Reason**: Gold deja de guardar datasets de modelado; el conjunto de features vive en el feature store (`data/silver/`).
**Migration**: Ver «El feature engineering ocurre después del split y se ajusta solo con train».

### Requirement: Las features de gold son transformaciones deterministas por fila
**Reason**: Las features derivadas se calculan ahora dentro del pipeline de preprocesamiento, después del split.
**Migration**: Ver «El pipeline de preprocesamiento es un artefacto reproducible».

### Requirement: La paridad entrenamiento/serving aún no es verificable
**Reason**: El pipeline guardado ya permite verificar la paridad del preprocesamiento.
**Migration**: Ver la comprobación `train-serve-parity` del requisito del pipeline.
