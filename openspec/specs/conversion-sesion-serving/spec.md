# conversion-sesion-serving Specification

## Purpose
TBD - created by archiving change conversion-sesion-deploy-monitoring. Update Purpose after archive.
## Requirements
### Requirement: El modelo servido es la versión registrada elegida por parámetro

La función de despliegue SHALL cargar el modelo desde el Model Registry de MLflow por versión (`--model-version`) o por alias (`--model-alias`, por defecto `champion`), y SHALL registrar en cada inferencia el nombre, la versión y el `run_id` del modelo usado. Cambiar de modelo SHALL requerir solo cambiar ese parámetro.

#### Scenario: Se elige otra versión

- **WHEN** se ejecuta la función con `--model-version 1` y luego con `--model-version 2`
- **THEN** las inferencias del primer lote llevan `model_version = 1` y las del segundo `model_version = 2`, con su `run_id` respectivo

```yaml contract
gate: contract-compat
registered_model: conversion-sesion
assert:
  - check: version_selectable
    versions: [1, 2]
  - check: default_alias
    value: champion
```

### Requirement: El contrato de entrada y salida es el de la signature

El modelo registrado SHALL aceptar sesiones crudas con las columnas y tipos declarados y devolver la probabilidad de conversión. Una fila que incumpla el contrato SHALL quedar registrada con `status = rejected` y su motivo, sin detener el lote.

#### Scenario: Fila inválida en el lote

- **WHEN** una sesión llega sin la columna `route`
- **THEN** esa fila se registra como `rejected` y las demás filas del lote se predicen con normalidad

```yaml contract
gate: contract-compat
assert:
  - check: signature_matches_spec
    inputs:
      num_passengers: long
      sales_channel: string
      trip_type: string
      purchase_lead: long
      length_of_stay: long
      flight_hour: long
      flight_day: string
      route: string
      booking_origin: string
      wants_extra_baggage: long
      wants_preferred_seat: long
      wants_in_flight_meals: long
      flight_duration: double
  - check: invalid_row_rejected_batch_continues
```

### Requirement: Cada inferencia se guarda en Gold con lo necesario para monitorear

Cada inferencia SHALL guardarse en `data/gold/inferences/` (un Parquet por lote) con: `inference_id`, `batch_id`, `timestamp_utc`, `source` (`cli` o `simulation`), `model_name`, `model_version`, `model_run_id`, `prob_conversion`, `intervene`, `decision_threshold`, `latency_ms`, `status` y **todas las columnas de entrada** con prefijo `in_`, para poder medir data drift.

#### Scenario: El registro es completo

- **WHEN** se ejecuta la función con 3 filas
- **THEN** el Parquet del lote tiene 3 registros con todas esas columnas y ninguna nula, salvo el motivo de rechazo

```yaml contract
gate: contract-compat
assert:
  - check: record_columns_present
    value: [inference_id, batch_id, timestamp_utc, source, model_name, model_version,
            model_run_id, prob_conversion, intervene, decision_threshold, latency_ms, status]
  - check: inputs_stored_with_prefix
    prefix: in_
```

### Requirement: La decisión de intervenir usa el K de la spec de evaluation

La decisión `intervene` SHALL ser verdadera cuando la probabilidad iguala o supera el umbral guardado como etiqueta de la versión registrada, calculado como el cuantil `1 - K` de las puntuaciones de test del candidato, con K tomado de `conversion-sesion-evaluation` (20 %).

#### Scenario: El umbral corresponde a K

- **WHEN** se aplica el umbral a las puntuaciones de test
- **THEN** interviene una fracción de sesiones igual a K, con tolerancia de 1 punto porcentual

```yaml contract
gate: contract-compat
assert:
  - check: threshold_matches_k
    k_fraction: 0.20
    tolerance: 0.01
```

### Requirement: La latencia p99 por sesión es de 250 ms o menos

Con el modelo cargado y precalentado, la inferencia de una sola sesión SHALL tener latencia p99 de 250 ms o menos en local, medida sobre 200 sesiones.

#### Scenario: Latencia medida

- **WHEN** el gate ejecuta 200 inferencias de una fila
- **THEN** el percentil 99 no supera 250 ms

```yaml contract
gate: latency-p99
sessions: 200
assert:
  - metric: p99_ms
    op: "<="
    value: 250
```

### Requirement: Volver a la versión anterior es un cambio de parámetro

Reapuntar el alias a la versión anterior SHALL bastar para revertir: la siguiente inferencia SHALL usar esa versión, y volver a la nueva SHALL ser igual de directo.

#### Scenario: Simulacro de rollback

- **WHEN** el gate apunta un alias de prueba a la versión 1, infiere, lo apunta a la versión 2 y vuelve a inferir
- **THEN** cada inferencia informa la versión esperada y ninguna falla

```yaml contract
gate: rollback-drill
registered_model: conversion-sesion
assert:
  - check: alias_flip_changes_served_version
    versions: [1, 2]
  - check: no_failed_inference
```

### Requirement: Solo se promueve con comprobante

El alias `champion` SHALL asignarse únicamente a una versión con un comprobante que ligue spec pack, dataset, código, entorno, modelo y `run_id`, con todos los gates aplicables en verde y el hash del modelo igual al del artefacto registrado. La línea base SHALL poder marcarse como destino de rollback sin comprobante propio.

#### Scenario: Promoción sin comprobante

- **WHEN** se intenta promover una versión sin comprobante válido
- **THEN** la promoción se rechaza y el alias no cambia

```yaml contract
gate: contract-compat
assert:
  - check: promotion_receipt_valid
    identities: [spec_pack, dataset, code, environment, model]
```

