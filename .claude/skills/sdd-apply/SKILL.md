---
name: sdd-apply
description: "Implementar las tareas de un change y sellar el candidato entrenado. No evalúa su propio resultado. Trigger: el orquestador lanza la implementación con tasks.md listo."
metadata:
  version: "1.0"
  phase: apply
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-apply` salvo que hayas cargado este skill
directamente. Como orquestador, delega.

**No ejecutes la fase de verificación**, ni siquiera si el resultado parece obvio.

## Language Domain Contract

El código, los comentarios y los mensajes de commit se escriben en **inglés** por defecto.

## Purpose

Implementas contra los delta specs y las tareas, y **sellas el candidato** en cuanto termina el
entrenamiento.

## What to Do

### Paso 1 — Cargar el contexto desde el CLI

```bash
openspec status --change <nombre> --json
openspec instructions apply --change <nombre> --json
```

Lee **todos** los `contextFiles` que devuelve. No asumas nombres de archivo.

### Paso 2 — Implementar tarea a tarea

Marca `- [ ]` → `- [x]` inmediatamente al completar cada una. Cambios mínimos y acotados a la
tarea.

### Paso 3 — Sellar, antes de mirar ninguna métrica

```bash
python gates/seal.py --change <nombre>
```

Congela cinco identidades: `spec_pack`, `dataset`, `code`, `env`, `model`. En ML el commit no
identifica la versión —el mismo código sobre otro snapshot produce otro modelo—, así que "la
misma versión" solo queda definida por las cinco juntas.

Si el árbol de trabajo está sucio el sellado **falla**, y eso es correcto: un candidato no
reproducible no se promueve. Limpia y vuelve a sellar; **no fuerces**.

## Rules

- **No juzgas tu propio resultado.** `apply` nunca ejecuta los gates de aceptación ni declara que
  un change está listo. Si el mismo razonamiento que produjo un candidato decide si es aceptable,
  la verificación no informa nada. Si te piden "ya que estás, comprueba si pasa", devuelve el
  control.
- **Nunca escribas en `openspec/specs/`.** Un hook lo bloquea; si lo encuentras bloqueado no es
  un error de configuración, es el diseño funcionando. El cambio va en el delta.
- Semilla y entorno fijados según la capability `training`.
- Si descubres que el contrato de datos está mal, **para**: es otro change sobre `<modelo>-data`,
  no un arreglo silencioso por el camino.
- Si la implementación revela un problema de diseño, para y propón actualizar el artefacto.
- Aplica `rules.apply` de `openspec/config.yaml`.

## Return Summary

Tareas completadas, progreso `N/M`, el sellado emitido, y qué falta. Si quedó bloqueado, por qué.
