## ADDED Requirements

### Requirement: El data drift se mide con PSI contra el conjunto de entrenamiento

El monitoreo SHALL calcular el PSI de cada feature de entrada y de la puntuación del modelo, sobre una ventana de al menos 200 inferencias con `status = ok`, contra la distribución de `train`. Numéricas: 10 intervalos por cuantiles de train. Categóricas: categorías con al menos 1 % de train y «otros». Severidad: aviso con PSI ≥ 0,10 y alerta con PSI ≥ 0,25. Con menos de 200 inferencias el resultado es «datos insuficientes», no verde.

#### Scenario: Ventana sin desvío

- **WHEN** la ventana se extrae de la misma distribución que train
- **THEN** ninguna feature alcanza el nivel de alerta

```yaml contract
gate: false-positive-budget
reference: data/silver/train.parquet
window_size: 200
windows: 200
seed: 42
rule:
  warn_psi: 0.10
  alert_psi: 0.25
assert:
  - metric: alert_rate_no_drift
    op: "<="
    value: 0.05
```

### Requirement: Una alerta de drift detecta un desvío real

La regla de alerta SHALL detectar un desvío inyectado (sobremuestreo cinco veces mayor de `sales_channel = Mobile`) en al menos el 90 % de las ventanas.

#### Scenario: Ventana con desvío

- **WHEN** la ventana se extrae con el desvío inyectado
- **THEN** la regla dispara alerta en al menos el 90 % de las ventanas

```yaml contract
gate: alert-backtest
reference: data/silver/train.parquet
window_size: 200
windows: 200
seed: 42
drift_scenario:
  column: sales_channel
  value: Mobile
  oversample_factor: 5
assert:
  - metric: detection_rate_with_drift
    op: ">="
    value: 0.90
```

### Requirement: Las métricas de producto tienen ventana, umbral, severidad y acción

El monitoreo SHALL evaluar las señales siguientes, cada una con su umbral y la acción esperada.

| Señal | Ventana | Aviso | Alerta | Acción |
|---|---|---|---|---|
| PSI de feature o de puntuación | 200 inferencias | ≥ 0,10 | ≥ 0,25 | investigar el origen del desvío; si persiste, abrir un change de reentrenamiento |
| Latencia p99 por sesión | 200 inferencias | > 250 ms | > 500 ms | revisar carga y tamaño del modelo |
| Tasa de rechazo | 200 inferencias | > 1 % | > 5 % | revisar el contrato de entrada con el productor de datos |
| Categorías no vistas (`route`, `booking_origin`) | 200 inferencias | > 5 % | > 15 % | reentrenar con las nuevas categorías |
| Tasa de intervención frente a K | 200 inferencias | ±5 pp | ±10 pp | revisar umbral y distribución de puntuaciones |

#### Scenario: Se evalúan todas las señales

- **WHEN** se genera el resumen de monitoreo
- **THEN** cada señal de la tabla aparece con su estado (`ok`, `aviso`, `alerta` o `datos insuficientes`)

```yaml contract
gate: alert-backtest
assert:
  - check: signals_present
    value: [psi_features, psi_score, latency_p99, rejection_rate, unseen_categories, intervention_rate]
```

### Requirement: La evaluación por segmento se refleja en monitoreo

El monitoreo SHALL reportar la tasa de intervención y la puntuación media por canal de venta, tipo de viaje y tramo de antelación, los mismos segmentos de `conversion-sesion-evaluation`.

#### Scenario: Segmentos presentes

- **WHEN** se genera el resumen de monitoreo
- **THEN** existen métricas para los tres segmentos

```yaml contract
gate: alert-backtest
assert:
  - check: slices_present
    value: [sales_channel, trip_type, purchase_lead_bucket]
```

### Requirement: El dashboard es un HTML autocontenido generado desde Gold

El dashboard SHALL ser un único archivo HTML que funcione sin red, construido desde `data/gold/inferences/` con la marca aplicada, y SHALL usar la misma lógica de alertas que el backtest.

#### Scenario: Dashboard sin dependencias externas

- **WHEN** se abre `results/07_operation_and_monitoring/dashboard.html` sin conexión
- **THEN** muestra volumen, versión servida, latencia, drift, categorías no vistas, intervención y segmentos, y no referencia ninguna URL externa

```yaml contract
gate: alert-backtest
dashboard: results/07_operation_and_monitoring/dashboard.html
assert:
  - check: dashboard_offline
  - check: dashboard_panels
    value: [volume, model_version, latency, drift, unseen_categories, intervention, slices]
```
