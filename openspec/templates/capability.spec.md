# <modelo>-<aspecto>

## Purpose

<Qué gobierna esta capability y por qué existe. Una o dos frases.>

## Requirements

### Requirement: <enunciado en una frase, con SHALL>

El sistema SHALL <lo que debe ser cierto>.

#### Scenario: <caso concreto>

- **WHEN** <condición observable>
- **THEN** <resultado esperado>

```yaml contract
# El recorte comprobable del requisito. Lo lee el gate; si falta, el requisito
# es prosa y debe llevar `non_binding: true`.
gate: <nombre del gate en gates/>
assert:
  - metric: <nombre>
    op: "<=" 
    value: 0
    relative_to_baseline: true
```
