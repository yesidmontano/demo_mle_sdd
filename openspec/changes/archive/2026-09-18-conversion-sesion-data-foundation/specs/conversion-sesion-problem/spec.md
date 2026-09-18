## ADDED Requirements

### Requirement: Los objetivos de negocio y de ML se declaran por separado

El enunciado del problema SHALL declarar el objetivo de negocio y el objetivo de ML como elementos distintos, y SHALL expresar la traducción entre ambos como un supuesto explícito.

#### Scenario: Los objetivos son revisables

- **WHEN** una persona revisora abre la capability `problem`
- **THEN** el objetivo de negocio, el objetivo de ML, la métrica de decisión y el ticket medio supuesto aparecen cada uno una sola vez y por separado

```yaml contract
gate: human-review
assert:
  - field: business_objective
    value: "ingreso incremental por sesión intervenida, presupuesto fijo"
  - field: ml_objective
    value: "P(booking_complete | atributos de la sesión) calibrada"
  - field: decision_metric
    value: "conversiones capturadas en el top-K del ranking"
  - field: optimization_metric
    value: "log-loss o PR-AUC; nunca accuracy"
  - field: average_ticket
    value: "supuesto, no medido; el dataset no tiene tarifa"
```

### Requirement: Los no-objetivos son explícitos antes de entrenar

El enunciado del problema SHALL listar lo que el modelo no hace.

#### Scenario: Se rechazan peticiones fuera de alcance

- **WHEN** alguien pide estimar el ingreso por sesión o el efecto de una intervención
- **THEN** la petición queda fuera de alcance porque el dataset no tiene tarifa ni intervención observada

```yaml contract
gate: human-review
assert:
  - field: non_goals
    contains: ["uplift", "ingreso por sesión", "historial de cliente"]
```
