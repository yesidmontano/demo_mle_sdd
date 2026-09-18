## ADDED Requirements

### Requirement: La regla de decisión es el top-K del ranking

La intervención SHALL aplicarse a la fracción K de sesiones con mayor probabilidad predicha, con K = 20 % como supuesto de presupuesto. Cambiar K SHALL requerir un change nuevo.

#### Scenario: K está declarado y se usa

- **WHEN** la evaluación calcula las conversiones capturadas
- **THEN** usa exactamente `k_fraction` de esta spec y no una constante propia del código

```yaml contract
gate: slice-eval
decision:
  k_fraction: 0.20
  metric: captured_conversions_at_k
```

### Requirement: Solo se evalúa el candidato sellado y registrado en MLflow

El modelo evaluado SHALL ser el sellado en `evidence/seal.json`, con el mismo hash de artefacto, registrado en MLflow con `signature` y flavor `sklearn`, y el sellado SHALL ser anterior a cualquier métrica de test.

#### Scenario: El sello no coincide

- **WHEN** el hash del modelo cargado difiere del de `seal.json`, o el run de MLflow no tiene `signature`
- **THEN** la evaluación se rechaza y el gate bloquea

```yaml contract
gate: slice-eval
seal: openspec/changes/conversion-sesion-modeling-evaluation/evidence/seal.json
assert:
  - check: model_hash_matches_seal
  - check: mlflow_signature_present
  - check: sealed_before_test_metrics
```

### Requirement: El candidato no es peor que la línea base, global ni por segmento

El candidato SHALL igualar o superar a la línea base en PR-AUC y en conversiones capturadas en el top-K sobre test, y en cada segmento con al menos 500 sesiones su PR-AUC SHALL no ser inferior al de la línea base en más de 0,02. Los segmentos son canal de venta, tipo de viaje y tramo de antelación.

#### Scenario: Se compara segmento a segmento

- **WHEN** el gate calcula las métricas del candidato y de la línea base sobre test
- **THEN** ningún segmento con 500 o más sesiones retrocede más de 0,02 de PR-AUC frente a la línea base

```yaml contract
gate: slice-eval
dataset: data/silver/test.parquet
slices: [sales_channel, trip_type, purchase_lead_bucket]
min_slice_size: 500
assert:
  - metric: pr_auc
    scope: global
    op: ">="
    relative_to_baseline: true
    tolerance: 0.0
  - metric: captured_conversions_at_k
    scope: global
    op: ">="
    relative_to_baseline: true
    tolerance: 0.0
  - metric: pr_auc
    scope: slice
    op: ">="
    relative_to_baseline: true
    tolerance: -0.02
```

### Requirement: Las probabilidades están calibradas

El error de calibración esperado (ECE) del candidato SHALL ser como máximo 0,05 sobre test, porque el ranking solo es útil si la probabilidad significa lo que dice.

#### Scenario: Calibración medida

- **WHEN** se calcula el ECE con 10 intervalos sobre test
- **THEN** es menor o igual que 0,05

```yaml contract
gate: slice-eval
dataset: data/silver/test.parquet
assert:
  - metric: ece
    scope: global
    op: "<="
    value: 0.05
```

### Requirement: El comportamiento del modelo es coherente

El candidato SHALL producir probabilidades válidas, tolerar categorías no vistas y responder en la dirección esperada a las banderas `wants_*`.

#### Scenario: Pruebas de comportamiento

- **WHEN** se ejecutan las pruebas sobre una muestra de test
- **THEN** todas las probabilidades están en [0, 1] y suman 1 por fila, una categoría de `booking_origin` no vista no rompe la predicción, y activar las tres banderas `wants_*` no reduce la probabilidad media

```yaml contract
gate: behavioral-tests
dataset: data/silver/test.parquet
assert:
  - test: probabilities_valid
  - test: unseen_category_tolerated
  - test: wants_flags_directional
    tolerance: 0.0
```

### Requirement: La línea base es reproducible

Reentrenar la línea base con el mismo código, datos y semilla SHALL reproducir su log-loss en test.

#### Scenario: Se reejecuta la línea base

- **WHEN** el gate reentrena la línea base desde cero
- **THEN** su log-loss en test difiere del registrado en menos de 1e-6

```yaml contract
gate: incumbent-rerun
dataset: data/silver/test.parquet
assert:
  - metric: log_loss_abs_diff
    op: "<="
    value: 1.0e-6
```

### Requirement: La evaluación por segmento se refleja en monitoreo

Los segmentos declarados aquí SHALL trasladarse a `conversion-sesion-monitoring` cuando se especifique ese aspecto.

#### Scenario: Segmentos pendientes de trasladar

- **WHEN** se abra el change de monitoreo
- **THEN** debe declarar señales para canal de venta, tipo de viaje y tramo de antelación

```yaml contract
non_binding: true
reason: la capability de monitoring aún no existe (fase 07)
```
