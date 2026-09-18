## ADDED Requirements

### Requirement: Gold solo contiene features conocidas al predecir

La capa `gold` SHALL contener el objetivo `booking_complete` y solo features conocidas mientras la sesión sigue abierta. Las banderas `wants_*` SHALL admitirse únicamente si la exploración muestra que se seleccionan durante la sesión y no se rellenan al completarla.

#### Scenario: Se verifica la fuga de las banderas

- **WHEN** la exploración compara `wants_*` entre sesiones convertidas y no convertidas
- **THEN** las banderas se conservan si las sesiones no convertidas muestran tasas distintas de cero, y se descartan en caso contrario

```yaml contract
gate: leakage-check
dataset: data/gold/sessions.parquet
assert:
  - metric: single_feature_auc
    op: "<"
    value: 0.85
    applies_to: all_features
  - metric: forbidden_columns_present
    op: "=="
    value: 0
    forbidden: [booking_complete_copy]
```

### Requirement: Las features de gold son transformaciones deterministas por fila

Las features derivadas en gold SHALL depender solo de la misma fila, de modo que ningún estadístico se aprenda del dataset completo antes del split entrenamiento/prueba. Las codificaciones aprendidas (target encoding de `route` y `booking_origin`) se difieren al modelado.

#### Scenario: Features derivadas

- **WHEN** gold se construye desde silver
- **THEN** `purchase_lead_bucket`, `is_weekend_flight` y `extras_count` están presentes y se calculan solo con columnas de la misma fila

```yaml contract
gate: leakage-check
dataset: data/gold/sessions.parquet
assert:
  - metric: columns_present
    value: [purchase_lead_bucket, is_weekend_flight, extras_count]
```

### Requirement: La paridad entrenamiento/serving aún no es verificable

Este change no tiene camino de serving, por lo que el requisito de paridad SHALL declararse en el change de `serving` que lo introduzca.

#### Scenario: Paridad diferida

- **WHEN** se abre un change de serving
- **THEN** debe reutilizar el mismo código de transformación de gold y pasar `train-serve-parity`

```yaml contract
non_binding: true
reason: todavía no existe camino de serving
```
