## ADDED Requirements

### Requirement: Silver es el feature store y guarda el split

La capa `data/silver/` SHALL ser el feature store: además del dataset limpio, SHALL guardar los conjuntos de entrenamiento y prueba, antes y después de la transformación, el pipeline de preprocesamiento ajustado y un manifiesto de reproducibilidad.

#### Scenario: El feature store está completo

- **WHEN** termina la fase de preparación de datos
- **THEN** existen `sessions`, `train`, `test`, `train_features`, `test_features`, `preprocessing_pipeline.joblib` y `manifest.json` en `data/silver/`

```yaml contract
gate: data-contract
assert:
  - metric: files_present
    value:
      - data/silver/sessions.parquet
      - data/silver/train.parquet
      - data/silver/test.parquet
      - data/silver/train_features.parquet
      - data/silver/test_features.parquet
      - data/silver/preprocessing_pipeline.joblib
      - data/silver/manifest.json
```

### Requirement: El split es estratificado, reproducible y sin solapamiento

El split SHALL ser 80/20, estratificado por `booking_complete`, con semilla fija registrada en el manifiesto, y ninguna fila SHALL aparecer en ambos conjuntos.

#### Scenario: El split se verifica

- **WHEN** el gate corre sobre `train.parquet` y `test.parquet`
- **THEN** la tasa de positivos difiere en menos de 0,5 puntos porcentuales entre ambos y no hay filas compartidas

```yaml contract
gate: data-contract
train: data/silver/train.parquet
test: data/silver/test.parquet
assert:
  - metric: split_positive_rate_gap
    op: "<="
    value: 0.005
  - metric: split_overlap_rows
    op: "=="
    value: 0
  - metric: test_fraction
    op: between
    value: [0.19, 0.21]
```

### Requirement: Train y test cumplen el esquema de silver

Los conjuntos `train.parquet` y `test.parquet` SHALL cumplir los mismos rangos, valores y nulabilidad que `sessions.parquet`.

#### Scenario: Esquema de los conjuntos

- **WHEN** el gate `data-contract` corre sobre train y test
- **THEN** no hay nulos ni duplicados y todas las columnas están dentro de sus rangos y valores declarados

```yaml contract
gate: data-contract
datasets: [data/silver/train.parquet, data/silver/test.parquet]
assert:
  - metric: null_count
    op: "=="
    value: 0
  - metric: duplicate_rows
    op: "=="
    value: 0
  - column: booking_complete
    values: [0, 1]
  - column: num_passengers
    range: [1, 9]
  - column: flight_hour
    range: [0, 23]
  - column: flight_duration
    range: [4, 10]
  - column: purchase_lead
    range: [0, 900]
  - column: sales_channel
    values: [Internet, Mobile]
  - column: trip_type
    values: [RoundTrip, OneWay, CircleTrip]
  - column: flight_day
    values: [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
```

### Requirement: Gold queda reservada a inferencia

La capa `data/gold/` NO SHALL contener datasets de entrenamiento ni de evaluación; SHALL reservarse a datos de inferencia y a pruebas de despliegue.

#### Scenario: Gold sin datasets de modelado

- **WHEN** termina la preparación de datos
- **THEN** `data/gold/` no contiene archivos de datos

```yaml contract
gate: data-contract
assert:
  - metric: gold_data_files
    op: "=="
    value: 0
```
