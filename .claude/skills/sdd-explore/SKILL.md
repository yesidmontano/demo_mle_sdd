---
name: sdd-explore
description: "Investigar datos, fuentes y enfoques antes de comprometer un change. Trigger: el orquestador necesita entender el material antes de especificar."
metadata:
  version: "1.0"
  phase: explore
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-explore` salvo que hayas cargado este
skill directamente. Como orquestador, delega.

## Language Domain Contract

Los artefactos técnicos se escriben en **inglés** por defecto. Los resúmenes a la persona siguen
el idioma de la conversación.

## Purpose

Exploras el material —datos, fuentes, enfoques— y produces un **hallazgo archivable**. No
modificas el contrato ni escribes código de producción.

`openspec-explore` piensa sobre requisitos. Aquí la exploración recae además sobre los datos, que
es donde vive la mayor parte de la incertidumbre de un proyecto de ML.

## What to Do

### Paso 1 — Abrir el change

```bash
openspec new change <nombre-kebab>
mkdir -p openspec/changes/<nombre>/evidence
```

Un change de exploración **no lleva delta specs**. No cambia el contrato.

### Paso 2 — Explorar contra el contrato, no en el vacío

Si existe `openspec/specs/<modelo>-data/spec.md`, léelo primero. Exploras para comprobar o
refutar algo declarado, no para mirar los datos a ver qué sale.

### Paso 3 — Escribir `evidence/finding.md`

| Sección | Qué contiene |
|---|---|
| Question | La pregunta, **escrita antes de mirar los datos** |
| Scope | Tabla, ventana temporal, filas, filtros |
| Result | El resultado con los números que lo sostienen |
| Ruled out | **Qué queda descartado y bajo qué condiciones** |
| Next | Qué change sugiere abrir, si sugiere alguno |

## Rules

- Declara ventana temporal y tamaño de muestra en cada afirmación. Un número sin su denominador
  no es evidencia.
- Si encuentras una violación del contrato vigente, **eso es el hallazgo**: no lo arregles por el
  camino. Es un change sobre `<modelo>-data`.
- No escribas en `openspec/specs/`. Un hook lo bloquea.
- Nada de notebooks en el flujo gobernado: la exploración vive en el change.

## Por qué esto archiva

Un análisis exploratorio es un change como cualquier otro y **cierra con `sdd-archive`**, aunque
no fusione nada. Es exactamente el trabajo que hoy se evapora en notebooks y que el equipo repite
seis meses después. **Un resultado negativo archivado vale tanto como uno positivo.**

## Return Summary

La pregunta, el resultado, qué queda descartado, y si procede abrir un change que sí toque el
contrato.
