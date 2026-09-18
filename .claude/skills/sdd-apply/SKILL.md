---
name: sdd-apply
description: Implementar las tareas de un change y sellar el candidato entrenado. No evalúa ni aprueba su propio resultado. Usar cuando el delta y las tareas están listos.
---

# Implementar — `openspec-apply-change` con sellado

Sigue el bucle de `openspec-apply-change` sin cambios:

```bash
openspec status --change <nombre> --json
openspec instructions apply --change <nombre> --json
```

Lee todos los `contextFiles` que devuelve el CLI, implementa tarea a tarea y marca
`- [ ]` → `- [x]` inmediatamente al completar cada una.

## Las dos reglas que este skill añade

**1. No juzgas tu propio resultado.** `apply` nunca ejecuta los gates de aceptación ni declara
que un change está listo. Eso es `sdd-verify`, en otro contexto. La razón no es procedimental: si
el mismo razonamiento que produjo un candidato decide si es aceptable, la verificación no informa
nada. Si te piden "ya que estás, comprueba si pasa" — devuelve el control.

**2. Sella el candidato en cuanto termine el entrenamiento**, antes de mirar una sola métrica:

```bash
python gates/seal.py --change <nombre>
```

Congelar antes de leer es el punto entero del mecanismo: así la evidencia pertenece a la versión
exacta que se promueve. Si el árbol de trabajo está sucio el sellado falla, y eso es correcto —
un candidato no reproducible no se promueve. Limpia y vuelve a sellar; no fuerces.

## Límite de escritura

Nunca `openspec/specs/`. Un hook lo bloquea, y si lo encuentras bloqueado no es un error de
configuración: es el diseño funcionando. El cambio va en el delta del change.

Si descubres que el contrato de datos está mal, **para**: es un change sobre la capability
`<modelo>-data`, no un arreglo silencioso por el camino.
