# conversion-sesion-data Specification

## Purpose
TBD - created by archiving change conversion-sesion-data-foundation. Update Purpose after archive.
## Requirements
### Requirement: Silver cumple el contrato de datos

La capa `silver` SHALL ser reproducible desde `bronze` con código del repositorio y SHALL cumplir el esquema, los rangos y la nulabilidad siguientes.

#### Scenario: Silver se valida

- **WHEN** el gate `data-contract` corre sobre `data/silver/sessions.parquet`
- **THEN** cada columna tiene el dtype y el rango declarados, no hay nulos y no hay filas duplicadas exactas

```yaml contract
gate: data-contract
dataset: data/silver/sessions.parquet
assert:
  - metric: null_count
    op: "=="
    value: 0
  - metric: duplicate_rows
    op: "=="
    value: 0
  - metric: row_count
    op: ">="
    value: 40000
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

### Requirement: Bronze es inmutable y el balance de clases está declarado

Ningún script SHALL escribir en `data/bronze/`, y la tasa de positivos de `booking_complete` SHALL declararse para que su deriva sea detectable.

#### Scenario: Se comprueba la tasa de positivos

- **WHEN** el gate corre sobre silver
- **THEN** la tasa de positivos está a menos de 3 puntos porcentuales del valor observado en la exploración (cerca del 15 %)

```yaml contract
gate: data-contract
dataset: data/silver/sessions.parquet
assert:
  - metric: positive_rate
    op: between
    value: [0.12, 0.18]
```

### Requirement: La frescura no es exigible en este dataset

El dataset no trae fecha absoluta, por lo que NO SHALL afirmarse una cota de frescura.

#### Scenario: Frescura diferida

- **WHEN** una fuente viva reemplaza al CSV estático
- **THEN** un change nuevo añade el requisito de frescura

```yaml contract
non_binding: true
reason: dataset público estático, sin columna de fecha
```

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

