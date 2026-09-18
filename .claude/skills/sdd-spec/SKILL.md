---
name: sdd-spec
description: "Escribir la propuesta y los delta specs de un change contra el Spec Pack de un modelo. Trigger: el orquestador arranca un cambio que toca el contrato."
metadata:
  version: "1.0"
  phase: spec
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-spec` salvo que hayas cargado este skill
directamente. Como orquestador, delega.

## Language Domain Contract

Los artefactos técnicos —`proposal.md` y los delta specs— se escriben en **inglés** por defecto.

## Purpose

Produces `proposal.md` y los **delta specs**: qué cambia del contrato vigente y por qué. No
escribes código ni editas las main specs.

## What to Do

### Paso 1 — Crear el change y leer el orden de artefactos

```bash
openspec new change <nombre-kebab>
openspec status --change <nombre> --json
```

Usa `artifactPaths` y `applyRequires` del JSON. **No asumas rutas.**

### Paso 2 — Decidir la vía

Consulta el tier del modelo en `openspec/config.yaml` → `tiers`:

- **Vía abreviada** (tier 3, o cambio pequeño y entendido): solo `proposal.md`.
- **Ciclo completo**: proposal → specs → design → tasks.

Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos marcos.
**El tier decide, no el tamaño ni la incertidumbre.**

### Paso 3 — `proposal.md`

Problema · objetivo de negocio y objetivo de ML **por separado** · no-objetivos · enfoque ·
alternativa descartada · riesgo principal.

**El gate más barato del sistema va aquí: ¿esto se resuelve sin ML?** Una heurística o una regla
de negocio resuelven más casos de los que se admite. Si la respuesta es sí, dilo y para. Ese
juicio ahorra proyectos enteros.

### Paso 4 — Delta specs

En `openspec/changes/<nombre>/specs/<modelo>-<aspecto>/spec.md`:

~~~markdown
## ADDED Requirements

### Requirement: Segment threshold on high-demand routes

The system SHALL keep the high-demand segment MAE at or below the baseline.

#### Scenario: Candidate evaluation

- **WHEN** a candidate is evaluated on the test set
- **THEN** its MAE on `demand_tier == 'high'` does not exceed the baseline

```yaml contract
gate: slice-eval
assert:
  - slice: "demand_tier == 'high'"
    metric: MAE
    op: "<="
    value: 0
    relative_to_baseline: true
    min_support: 100
```
~~~

Secciones válidas: `## ADDED`, `## MODIFIED`, `## REMOVED`, `## RENAMED Requirements`.

### Paso 5 — Declarar el alcance con precisión

**Qué capabilities toca el delta decide qué gates se activan.** Declarar de menos salta
verificaciones; de más, paga gates que no aplican. Revísalo dos veces.

## Rules

- **El test de ejecutabilidad, a cada requisito:** *¿qué comando haría fallar esto?* Si no hay
  respuesta, `non_binding: true` dentro del bloque. Ningún requisito se queda en prosa sin marcar.
- Umbrales **relativos a la línea base vigente** siempre que puedas: un umbral absoluto envejece
  mal en un régimen no estacionario.
- Si tocas `evaluation`, umbrales **por slice**, no solo agregados. Un agregado que sube puede
  ocultar degradación en un subconjunto, y es el modo de falla más común y más caro.
- Un slice nuevo en `evaluation` **se refleja también en `monitoring`**. Si las dos listas
  divergen, la evaluación offline y la vigilancia online miden objetos distintos.
- Si tocas `features`, toda variable declara `offline_source` **y** `online_source`: es el único
  mecanismo estructural contra el train/serve skew.
- Nunca escribas en `openspec/specs/`. Un hook lo bloquea.
- Aplica `rules.specs` de `openspec/config.yaml`.

## Return Summary

Capabilities tocadas, gates que eso activará, y qué requisitos quedaron `non_binding`.
