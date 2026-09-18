# gates/ — los contratos, ejecutables

Cada gate es un **ejecutable independiente**, no una función dentro del pipeline. Esa separación
es deliberada: un gate que vive dentro del código que verifica puede desactivarse con un flag.

## Contrato de un gate

```
python gates/<nombre>.py --change <feature-id> [--model <modelo>]
```

- **stdout**: un JSON con `{gate, status, metrics, detail}`.
- **código de salida**: `0` pasa · distinto de `0` bloquea.
- **efecto**: escribe su salida en `openspec/changes/<feature-id>/evidence/<nombre>.json`.

Un gate lee su criterio del Spec Pack, nunca lo lleva escrito dentro. Si el umbral vive en el
código y no en la spec, la spec no gobierna nada.

## Plumbing (independiente del dominio)

| Archivo | Qué hace |
|---|---|
| `run.py` | resuelve `touches` → `gate_routing` y ejecuta solo los gates que aplican |
| `seal.py` | congela el candidato: cinco hashes. Falla si el árbol está sucio. Escribe `evidence/seal.json` |
| `receipt.py` | emite y verifica `evidence/receipt.json` |
| `merge.py` | aplica el delta al Spec Pack. Único punto que exporta `SDD_ARCHIVE=1` |

Los dos primeros son precondición de fase: `.claude/hooks/sdd_phase_guard.py` comprueba que
existan `evidence/seal.json` antes de `sdd-verify` y `evidence/receipt.json` antes de
`sdd-archive`.

## Gates de dominio

`data-contract` · `freshness` · `train-serve-parity` · `leakage-check` · `reproducibility` ·
`compute-budget` · `slice-eval` · `behavioral-tests` · `incumbent-rerun` · `contract-compat` ·
`latency-p99` · `rollback-drill` · `alert-backtest` · `false-positive-budget`

**Pendientes de implementar**: dependen del dataset y del modelo concretos, así que se escriben
después de elegir el dataset. Las skills ya los referencian por nombre.

## La prueba de que un gate sirve

Al escribirlo, encuentra el caso que lo hace fallar y déjalo en un test. Si no existe tal caso,
el gate no puede bloquear y es teatro de gobernanza: mejor decirlo que dejarlo verde.
