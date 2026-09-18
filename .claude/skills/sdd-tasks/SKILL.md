---
name: sdd-tasks
description: "Descomponer un change de ML en tareas ordenadas donde cada una deja un artefacto verificable. Trigger: el orquestador lanza la planificación tras el diseño."
metadata:
  version: "1.0"
  phase: tasks
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-tasks` salvo que hayas cargado este skill
directamente. Como orquestador, delega.

## Language Domain Contract

`tasks.md` se escribe en **inglés** por defecto.

## Purpose

Produces `openspec/changes/<nombre>/tasks.md`. **Planificas, no implementas.**

## What You Receive

Nombre del change, `proposal.md`, delta specs y `design.md`.

## What to Do

### Paso 1 — Ordenar por las dependencias reales del pipeline

```
Fase 1: Datos          ingesta · validación contra el contrato
Fase 2: Variables      construcción · paridad offline/online
Fase 3: Entrenamiento  split · entrenamiento · SELLADO
Fase 4: Evaluación     métricas por slice · tests de comportamiento
Fase 5: Servicio       contrato de E/S · degradación · reversión
```

**El sellado va en la fase 3, no en la 4.** El candidato se congela antes de que nada lo lea; si
la tarea de sellar aparece después de la de evaluar, el orden está mal y la evidencia describirá
algo que ya no existe.

### Paso 2 — Formato

```markdown
## Phase 2: Features

- [ ] 2.1 <acción concreta> → <artefacto que queda> (`<ruta>`)
- [ ] 2.2 <acción concreta> → <artefacto que queda> (`<ruta>`)
```

Numeración jerárquica. Cada tarea completable en **una sesión**: si necesita varias, son dos
tareas o es otro change.

### Paso 3 — Aplicar el criterio de verificabilidad

| Criterio | Ejemplo válido | Anti-ejemplo |
|---|---|---|
| **Concreta** | "Crear `gates/data_contract.py` que lea el bloque `contract` de `<modelo>-data`" | "Validar los datos" |
| **Deja artefacto** | "Ejecutar el gate y guardar su salida en `evidence/`" | "Comprobar que pasa" |
| **Verificable** | "Test: un snapshot de 30 h hace fallar `freshness`" | "Asegurarse de que funciona" |

**Cada tarea deja un artefacto verificable, no una afirmación.**

### Paso 4 — Una tarea de gate por cada capability tocada

Resuelve `gate_routing` contra los aspectos que toca el delta y crea una tarea por gate. Un gate
sin tarea es un gate que nadie escribirá.

Para cada gate nuevo, añade además **la tarea del caso que lo hace fallar**. Si al escribirlo no
existe tal caso, el gate no puede bloquear y es teatro de gobernanza.

## Rules

- Referencia rutas de archivo concretas. Nada de "el módulo de datos".
- Las tareas de test referencian escenarios concretos de los delta specs.
- Si `tasks.md` ya existe, **preserva la lista y la numeración**: añade o edita en su sitio, nunca
  reescribas el archivo desde cero.
- Nunca tareas vagas como "implementar la feature" o "añadir tests".
- Aplica `rules.tasks` de `openspec/config.yaml`.

## Return Summary

Tabla de fases con el número de tareas, el orden de implementación y por qué, y qué gates quedan
por escribir.
