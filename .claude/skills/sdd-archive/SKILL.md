---
name: sdd-archive
description: "Fusionar los delta specs a las main specs y cerrar el change. Trigger: el orquestador cierra un change con los gates en verde, o uno que termina sin despliegue."
metadata:
  version: "1.0"
  phase: archive
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-archive` salvo que hayas cargado este
skill directamente. Como orquestador, delega.

Junto con la sincronización que incluye esta fase, eres **el único autorizado a escribir en
`openspec/specs/`**.

## Language Domain Contract

Las main specs y el índice de promociones se escriben en **inglés** por defecto.

## Purpose

Cierras el change: **fusionas sus deltas a las main specs** (el paso que OpenSpec separa como
`sync-specs`) y lo mueves al archivo.

## Precondición innegociable

Existe `evidence/receipt.json`, verificable, con todos los gates que el alcance activó en verde.
**Sin comprobante no hay fusión.** Un hook lo comprueba al entrar en la fase; si te piden
archivar sin él, di que no y explica qué falta.

```bash
python gates/receipt.py --change <nombre> --verify
```

## What to Do — change que cambia el contrato

### Paso 1 — Comprobar que el comprobante sigue vigente

El `spec_pack` del comprobante debe coincidir con el estado actual de `openspec/specs/`. Si
alguien fusionó otra cosa entretanto, **el comprobante quedó obsoleto**: devuelve el control a
`sdd-verify` para rehacer la evaluación sobre las specs nuevas. **No fuerces la fusión.**

### Paso 2 — Fusionar los deltas, con criterio

```bash
openspec status --change <nombre> --json   # toma artifactPaths.specs.existingOutputPaths
```

Operación dirigida por el agente: se leen los deltas y se editan las main specs directamente, lo
que permite fusionar con criterio (añadir un escenario sin copiar el requisito entero).

| Sección del delta | Qué haces |
|---|---|
| `ADDED` | Si el requisito no existe, añadirlo. Si existe, tratarlo como `MODIFIED` |
| `MODIFIED` | Aplicar el cambio **preservando los escenarios no mencionados** |
| `REMOVED` | Quitar el bloque entero del requisito |
| `RENAMED` | Renombrar de `FROM:` a `TO:` |

Si la capability no existe todavía, créala con su `## Purpose` y los requisitos añadidos.

**Conserva el bloque ` ```yaml contract ` de cada requisito.** Es lo que hace ejecutable a la
spec: perderlo en la fusión la degrada a documentación y nadie lo nota hasta que un gate deja de
bloquear.

La escritura va por `gates/merge.py`, único punto que habilita la escotilla del hook.

### Paso 3 — Archivar

```bash
openspec archive <nombre>
```

Mueve el change a `openspec/changes/archive/<nombre>/` con su evidencia completa y registra el
comprobante en el índice de promociones.

## What to Do — change que NO despliega

Un análisis exploratorio o un experimento fallido **archivan igual**, sin deltas que fusionar:

1. `evidence/finding.md` con la conclusión y los datos que la sostienen.
2. Si el resultado es negativo, decir **qué se descarta y bajo qué condiciones**, para que nadie
   repita la investigación dentro de seis meses.
3. Mover a `openspec/changes/archive/<nombre>/`. Las main specs no cambian.

Esto no es burocracia añadida: es el trabajo que hoy se pierde en notebooks, recuperado sin
esfuerzo extra porque el flujo es el mismo para todo change.

## Rules

- Sin comprobante válido, no hay fusión. Sin excepciones.
- Archivar **no despliega y no aprueba**. Registra el estado real, incluido el trabajo inacabado
  si se archiva explícitamente. La política del repositorio y el tier deciden quién firma; el
  comprobante informa.
- Aplica `rules.archive` de `openspec/config.yaml`.

## Return Summary

Capabilities actualizadas y qué cambió en cada una, dónde quedó archivado el change, y el
comprobante registrado.
