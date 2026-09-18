---
name: sdd-explore
description: Investigar datos, fuentes y enfoques antes de comprometer un change. Produce un hallazgo archivable, no código. Usar para EDA, perfilado de calidad, estudios de sesgo y viabilidad.
---

# Explorar — extiende `openspec-explore` al material de ML

`openspec-explore` es un modo de pensamiento sobre requisitos. Aquí la exploración recae además
sobre **datos**, que es donde vive la mayor parte de la incertidumbre de un proyecto de ML.

## Qué produces

Un change **sin delta specs** y un hallazgo en `evidence/finding.md`:

```bash
openspec new change <nombre-kebab>
mkdir -p openspec/changes/<nombre>/evidence
```

El hallazgo lleva:

- La pregunta que se investigó, **escrita antes de mirar los datos**.
- Qué se miró exactamente: tabla, ventana temporal, filas, filtros.
- El resultado, con los números que lo sostienen.
- **Qué queda descartado y bajo qué condiciones.**
- Qué change sugiere abrir a continuación, si sugiere alguno.

## Cómo trabajas

- Antes de perfilar una fuente, lee `openspec/specs/<modelo>-data/spec.md` si existe: exploras
  contra un contrato, no en el vacío.
- Declara ventana temporal y tamaño de muestra en cada afirmación. Un número sin su denominador
  no es evidencia.
- Si encuentras una violación del contrato vigente, **eso es el hallazgo**: no lo arregles por el
  camino.

## Por qué esto archiva

Un análisis exploratorio es un change como cualquier otro. Sin delta specs no fusiona nada,
pero **deja rastro**. Es exactamente el trabajo que hoy se evapora en notebooks y que el equipo
repite seis meses después. Un resultado negativo archivado vale tanto como uno positivo.

Cierra con `sdd-archive`, no con `sdd-sync-specs`: no hay delta que fusionar.
