---
name: sdd-init
description: "Inicializar SDD para ML/MLOps en un proyecto y crear el Spec Pack de un modelo. Trigger: el orquestador arranca un proyecto nuevo o incorpora un modelo que ya está en producción."
metadata:
  version: "1.0"
  phase: init
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-init` salvo que hayas cargado este skill
directamente con la herramienta de skills.

- Si eres el subagente: continúa con el trabajo de fase. No delegues.
- Si cargaste el skill como orquestador: delega en el subagente correspondiente.

## Language Domain Contract

Los artefactos técnicos generados —specs, proposals, designs, tasks, mensajes de commit— se
escriben en **inglés** por defecto, con independencia del idioma de la conversación. Los
comentarios y resúmenes dirigidos a la persona siguen el idioma del contexto.

## Purpose

Dejas el proyecto listo para gobernarse por especificaciones: la estructura de OpenSpec, la
política del proyecto y las capabilities del primer modelo.

## What to Do

### Paso 1 — Inicializar OpenSpec

```bash
openspec init --tools claude
```

Crea `openspec/specs/` y `openspec/changes/archive/`. Si ya existen, no toques nada.

### Paso 2 — Escribir `openspec/config.yaml`

Tres bloques que el resto de fases consume:

- `tiers` — el corte entre la vía abreviada y el ciclo completo. Un modelo de tier 3 (interno,
  sin consumidores) no paga las ocho capabilities.
- `gate_routing` — qué gates activa cada **aspecto** de capability. Esta tabla es la que hace
  mecánico al marco.
- `rules.<fase>` — la política por fase, que cada skill aplica.

### Paso 3 — Crear el Spec Pack del modelo

El Spec Pack son las capabilities que comparten prefijo `<modelo>-`. Ocho aspectos, en este orden
porque cada uno restringe al siguiente:

| Aspecto | Gobierna |
|---|---|
| `problem` | objetivo de negocio vs objetivo de ML, métrica de decisión, no-objetivos |
| `data` | esquema, tipos, rangos, nulabilidad, PII, frescura, linaje |
| `features` | definición point-in-time, fuente offline/online, paridad train/serve |
| `training` | dataset, splits, semilla, hiperparámetros, reproducibilidad |
| `evaluation` | umbrales por slice, tests de comportamiento, calibración, baseline |
| `serving` | esquema E/S, p99, degradación, trazabilidad |
| `monitoring` | señales, ventanas, umbrales, severidad y acción |
| `governance` | tier de riesgo, aprobadores, retención, rollback |

```bash
mkdir -p openspec/specs/<modelo>-data
cp openspec/templates/capability.spec.md openspec/specs/<modelo>-data/spec.md
```

### Paso 4 — Escribir cada requisito en dos capas

El escenario lo lee una persona; el bloque ` ```yaml contract ` lo ejecuta un gate:

~~~markdown
### Requirement: Snapshot freshness

The system SHALL reject a snapshot older than 24 hours.

#### Scenario: Stale snapshot

- **WHEN** the most recent snapshot is 30 hours old
- **THEN** the data gate blocks training

```yaml contract
gate: freshness
assert:
  - max_lag: 24h
    on_violation: block
```
~~~

### Paso 5 — Validar

```bash
openspec validate --specs
```

## El caso que más importa

**Un modelo que ya está en producción y no tiene specs.** Aquí `sdd-init` es el primer paso del
roadmap: escribir el contrato de lo que ya existe, **sin automatizar nada todavía**. Entrega una
línea base auditable y el equipo aprende el formato sin cambiar de hábitos.

Automatizar antes de contratar solo acelera la producción de decisiones no auditables.

## Rules

- Aplica el test de ejecutabilidad a cada requisito: *¿qué comando haría fallar esto?* Si no hay
  respuesta, márcalo `non_binding: true`. **Ningún requisito se queda en prosa sin marcar.**
- Umbrales relativos a la línea base vigente siempre que sea posible.
- Verifica tres coherencias que se rompen en silencio: los slices de `evaluation` y `monitoring`
  nombran los mismos segmentos; toda feature declara fuente offline **y** online; `problem` dice
  cómo se traduce la métrica de ML a la de negocio.
- La plantilla vive en `openspec/templates/`, nunca dentro de `specs/`: el CLI la validaría como
  una capability real.

## Return Summary

Capabilities creadas, tier asignado y qué requisitos quedaron `non_binding` y por qué.
