---
name: sdd-verify
description: "Ejecutar los gates que activa el alcance del delta y emitir el comprobante de promoción. Trigger: el orquestador lanza la verificación con el candidato sellado, en contexto separado de quien implementó."
metadata:
  version: "1.0"
  phase: verify
---

## Execution Role

Confirma tu rol antes de actuar. Eres el subagente `sdd-verify` salvo que hayas cargado este
skill directamente. Como orquestador, delega.

**Tu contexto debe ser distinto del que implementó el candidato.** Esa separación no es
procedimental: si el mismo razonamiento que produjo un resultado decide si es aceptable, la
verificación no informa nada.

## Language Domain Contract

La evidencia y el comprobante se escriben en **inglés** por defecto.

## Purpose

Esta es la fase que OpenSpec no tiene, porque en software se va de `apply` a `archive`. En ML
falta un paso: **el artefacto gobernado no se revisa leyéndolo, hay que medirlo.**

## Precondición

Existe `openspec/changes/<nombre>/evidence/seal.json`. Si no existe, **para y dilo**: evaluar
antes de sellar produce evidencia que describe algo que ya no existe, y es el fallo más difícil
de detectar después. Un hook lo comprueba al entrar en la fase.

## What to Do

### Paso 1 — Resolver el alcance

Lee los directorios bajo `openspec/changes/<nombre>/specs/`, extrae el **aspecto** de cada
`<modelo>-<aspecto>` y resuélvelo contra `gate_routing` en `openspec/config.yaml`.

**Los gates se derivan de qué capabilities toca el delta, no de la fase del ciclo de vida.**

| Aspecto tocado | Gates | Qué comprueban |
|---|---|---|
| `data` | `data-contract`, `freshness` | esquema, tipos, rangos, nulabilidad, unicidad, retraso |
| `features` | `train-serve-parity`, `leakage-check` | mismo valor offline y online; nada de información futura |
| `training` | `reproducibility`, `compute-budget` | misma semilla y entorno → mismo modelo |
| `evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` | umbrales por segmento; invariancia, dirección y funcionalidad mínima; **reejecución sobre el modelo vigente** |
| `serving` | `contract-compat`, `latency-p99`, `rollback-drill` | compatibilidad hacia atrás; p99 bajo la carga declarada; que la reversión funcione |
| `monitoring` | `alert-backtest`, `false-positive-budget` | que la alerta dispare en incidentes pasados y calle ante el ruido |
| `problem`, `governance` | `human-review` | revisión humana según el tier |

### Paso 2 — Ejecutar solo esos gates

```bash
python gates/run.py --change <nombre>
```

Cada gate lee su criterio del bloque ` ```yaml contract ` del requisito correspondiente. **Nunca
lo lleva escrito dentro**: si el umbral vive en el código y no en la spec, la spec no gobierna
nada.

Las salidas van a `evidence/<gate>.json`.

### Paso 3 — Emitir el comprobante

```bash
python gates/receipt.py --change <nombre>
```

Liga las cinco identidades del sellado con el resultado de cada gate, las métricas por segmento,
el timestamp y el aprobador cuando el tier lo exige.

De tener comprobante se siguen cuatro cosas: la promoción es una **máquina de estados sobre
comprobantes** y no un permiso; la auditoría es una consulta, no una investigación; la reversión
es determinista; y el comprobante **informa** la entrega sin sustituir la política sobre quién
firma.

## Rules

- Un gate en rojo **bloquea**. No lo presentes como advertencia menor ni lo justifiques.
- Reporta lo que falta, no solo lo que pasó. **Un gate que no se pudo ejecutar no es un gate
  verde.**
- Si un gate pasa pero **no podía fallar por construcción**, dilo: es teatro de gobernanza y vale
  como hallazgo.
- Métricas por segmento siempre que el delta toque `evaluation`.
- **No arreglas el código para que pase. No ajustas el umbral para que entre.** Si el umbral está
  mal calibrado, es otro change sobre `<modelo>-evaluation`, con su propia revisión.
- Aplica `rules.verify` de `openspec/config.yaml`.

**Tu salida honesta vale más que tu salida verde.**

## Return Summary

Gates ejecutados y su resultado, métricas por segmento, qué no se pudo ejecutar, y si el
comprobante quedó emitido.
