---
name: sdd-propose
description: "Redactar la propuesta de un change — intención, alcance y enfoque — antes de tocar specs o código. Trigger: el orquestador abre una unidad de trabajo tras la exploración."
metadata:
  version: "1.0"
  phase: propose
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-propose` salvo que hayas cargado este
skill directamente. Como orquestador, delega.

## Language Domain Contract

`proposal.md` se escribe en **inglés** por defecto, con independencia del idioma de la
conversación.

## Purpose

Produces `openspec/changes/<nombre>/proposal.md`: **qué se quiere y por qué**, antes de que exista
un solo contrato o una sola línea de código. Es el artefacto que decide si el trabajo merece
hacerse.

**No escribes specs, ni diseño, ni tareas.** Cada uno tiene su fase.

## What to Do

### Paso 1 — Crear el change y leer el orden de artefactos

```bash
openspec new change <nombre-kebab>
openspec status --change <nombre> --json
openspec instructions proposal --change <nombre> --json
```

Usa `artifactPaths` del JSON; **no asumas rutas**. Las instrucciones traen `context`, `rules` y
`template`: son restricciones para ti, **no contenido que copiar al archivo**.

### Paso 2 — Decidir la vía

Consulta el tier del modelo en `openspec/config.yaml` → `tiers`:

- **Vía abreviada** (tier 3, o cambio pequeño y entendido): la propuesta y su evidencia bastan;
  no habrá specs, design ni tasks.
- **Ciclo completo**: esta propuesta abre `sdd-spec` → `sdd-design` → `sdd-tasks`.

Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos marcos.
**El tier decide, no el tamaño ni la incertidumbre.**

### Paso 3 — Escribir la propuesta

| Sección | Qué responde |
|---|---|
| **Problem** | Qué falla hoy y para quién. Con un número si lo hay |
| **Business objective** | Qué decisión de negocio mejora, y en qué unidad se mide |
| **ML objective** | Qué predice el modelo, y **cómo se traduce** a la métrica de negocio |
| **Non-goals** | Qué queda explícitamente fuera. Sin esta sección el alcance se desborda |
| **Approach** | El enfoque propuesto, en un párrafo |
| **Alternative rejected** | Qué se descarta y por qué. Si no hay alternativa considerada, no está pensado |
| **Main risk** | El riesgo de *este* cambio, no riesgos genéricos de ML |

Objetivo de negocio y objetivo de ML **van separados y ambos rellenos**. Si no sabes traducir uno
al otro, dilo: eso es un hallazgo, no un detalle pendiente. Un modelo sin esa traducción no tiene
criterio de éxito, solo métricas.

### Paso 4 — Aplicar el gate más barato del sistema

Pregunta y responde en la propuesta: **¿esto se resuelve sin ML?**

Una heurística, una regla de negocio o un ordenamiento simple resuelven más casos de los que se
admite. Si la respuesta es sí, **dilo y para**. Ese juicio ahorra proyectos enteros y vale más
que cualquier modelo que pudieras entrenar después.

Declara también a qué se vuelve si el modelo no supera la línea base. Un enfoque sin plan de
retirada no está terminado.

## Rules

- Nada de prosa que no comprometa a algo verificable. La propuesta no lleva umbrales —eso es
  `sdd-spec`— pero sí lleva **decisiones**.
- Si el contexto es insuficiente para fijar el alcance, pregunta. Prefiere una decisión razonable
  y declarada a una propuesta vaga.
- No escribas en `openspec/specs/`. Un hook lo bloquea.
- Aplica `rules.proposal` de `openspec/config.yaml`.

## Return Summary

El problema, los dos objetivos y su traducción, los no-objetivos, la vía elegida y su tier, y si
el juicio de "¿hace falta ML?" recomienda seguir o parar.
