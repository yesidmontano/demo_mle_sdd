---
name: sdd-propose
description: Abrir un change con sus artefactos — proposal, delta specs, design y tasks — contra el Spec Pack de un modelo. Usar al empezar cualquier unidad de trabajo que cambie el contrato.
---

# Proponer — `openspec-propose` con las capabilities de ML

Sigue el flujo de `openspec-propose` y el CLI tal cual. Lo que añade este skill es **qué
capabilities existen en un proyecto de ML y cómo se escribe un requisito que puede fallar**.

## Procedimiento

1. **Crear el change y leer el orden de artefactos** — igual que en `openspec-propose`:
   ```bash
   openspec new change <nombre-kebab>
   openspec status --change <nombre> --json
   ```
   Usa `artifactPaths` y `applyRequires` del JSON; no asumas rutas.

2. **Decidir la vía** según el tier del modelo (`openspec/config.yaml` → `tiers`):
   - **Vía abreviada** (tier 3, o cambio pequeño y entendido): `proposal.md` + evidencia.
   - **Ciclo completo**: proposal → specs (delta) → design → tasks.

   Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos
   marcos. El tier es lo que decide, no el tamaño ni la incertidumbre.

3. **`proposal.md`** — sigue `rules.proposal`. El gate más barato del sistema va aquí:
   **¿esto se resuelve sin ML?** Si la respuesta es sí, dilo y para.

4. **Delta specs** en `openspec/changes/<nombre>/specs/<modelo>-<aspecto>/spec.md`, en el formato
   de OpenSpec:

   ```markdown
   ## ADDED Requirements

   ### Requirement: Umbral por segmento en rutas de alta demanda

   El sistema SHALL mantener el MAE del segmento de alta demanda igual o mejor que la línea base.

   #### Scenario: Evaluación de un candidato

   - **WHEN** se evalúa un candidato sobre el conjunto de prueba
   - **THEN** su MAE en `demand_tier == 'high'` no supera el de la línea base

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
   ```

   Secciones válidas: `## ADDED`, `## MODIFIED`, `## REMOVED`, `## RENAMED Requirements`.

5. **`design.md`** y **`tasks.md`** (ciclo completo) según `rules.design` y `rules.tasks`.

## Los ocho aspectos

`problem` · `data` · `features` · `training` · `evaluation` · `serving` · `monitoring` ·
`governance`. Una capability se nombra `<modelo>-<aspecto>`.

**Qué capabilities toca el delta decide qué gates se activan** (`gate_routing`). Sé exacto:
declarar de menos salta verificaciones; de más, paga gates que no aplican.

## El test que aplicas a cada requisito

Pregunta, literalmente: **¿qué comando haría fallar esto?**

- Hay respuesta → escribe el bloque ` ```yaml contract ` con el umbral, esquema o invariante.
- No hay respuesta → márcalo `non_binding: true` dentro del bloque. **Ningún requisito se queda
  en prosa sin marcar.**

Reglas de ML que no se negocian: umbrales relativos a la línea base cuando sea posible; en
`evaluation`, umbrales **por slice** y no solo agregados; un slice nuevo se refleja también en
`monitoring`, o la evaluación offline y la vigilancia online medirán objetos distintos.
