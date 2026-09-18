## ADDED Requirements

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
