---
name: sdd-design
description: "Decidir la arquitectura de un change de ML y registrar la alternativa descartada. Trigger: el orquestador lanza el diseño tras aprobarse los delta specs."
metadata:
  version: "1.0"
  phase: design
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-design` salvo que hayas cargado este
skill directamente. Como orquestador, delega.

## Language Domain Contract

`design.md` se escribe en **inglés** por defecto.

## Purpose

Produces `openspec/changes/<nombre>/design.md`. **Decides, no implementas.**

## What You Receive

Nombre del change, `proposal.md` y los delta specs. Léelos antes de decidir nada.

## What to Do

### Paso 1 — Resolver las cuatro decisiones de ML

| Decisión | De qué depende de verdad |
|---|---|
| **Batch o en línea** | De la latencia de la decisión de negocio, no de la moda |
| **Sin estado o con estado** | ¿Cada reentrenamiento parte de cero o continúa del anterior? |
| **Feature store: construir, comprar o ninguno** | De datos de uso reales. **Esta decisión se pospone** hasta tenerlos |
| **Dónde vive el cómputo** | Del presupuesto declarado en `training` |

### Paso 2 — Formato

Cada decisión lleva tres cosas: **qué se decide · por qué · qué alternativa se descarta y bajo qué
condición se reconsideraría.** Sin esa tercera parte no es una decisión, es una preferencia.

### Paso 3 — Nombrar lo que no se puede dejar implícito

Tres riesgos que, callados, reaparecen en producción como incidentes:

- **Train/serve skew.** El contrato de variables lo atenúa pero **no lo elimina** sin cómputo
  compartido. Si eliges no tener feature store, dilo y declara qué riesgo aceptas.
- **Retroalimentación degenerada.** Si las predicciones del modelo contaminan sus propias
  etiquetas futuras, nómbralo y reserva tráfico de control.
- **Latencia de etiqueta.** Si supera el ciclo de reentrenamiento, el reentrenamiento automático
  no aplica. Dilo aquí, no más adelante.

## Rules

- No propongas arquitectura que los delta specs no exijan. El diseño sirve al contrato.
- Si el diseño revela que un requisito es inviable, **para**: vuelve a `sdd-spec`, no lo
  reinterpretes por el camino.
- Aplica `rules.design` de `openspec/config.yaml`.

## Return Summary

Las decisiones tomadas con su alternativa descartada, y los riesgos declarados explícitamente.
