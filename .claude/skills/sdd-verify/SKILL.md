---
name: sdd-verify
description: Ejecutar los gates que activan las capabilities tocadas por el delta y reportar los hallazgos sin suavizarlos. Usar cuando el candidato está sellado, en un contexto distinto del que lo implementó.
---

# Verificar — el paso que OpenSpec no tiene

OpenSpec va de `apply` a `archive`. En ML falta un paso entre medias, porque el artefacto
gobernado no se revisa leyéndolo: **hay que medirlo**.

## Precondición

Existe `openspec/changes/<nombre>/evidence/seal.json`. Si no existe, **para y dilo**: evaluar
antes de sellar produce evidencia que describe algo que ya no existe, y es el fallo más difícil
de detectar después. Un hook comprueba esto al entrar en la fase.

## Enrutamiento por alcance

Los gates aplicables se derivan de **qué capabilities toca el delta**, no de la fase del ciclo de
vida. Lee los directorios bajo `openspec/changes/<nombre>/specs/`, extrae el aspecto de cada
`<modelo>-<aspecto>` y resuélvelo contra `gate_routing` en `openspec/config.yaml`:

| Aspecto tocado | Gates | Qué comprueban |
|---|---|---|
| `data` | `data-contract`, `freshness` | esquema, tipos, rangos, nulabilidad, unicidad, retraso máximo |
| `features` | `train-serve-parity`, `leakage-check` | que la misma definición dé el mismo valor offline y online; que no entre información futura |
| `training` | `reproducibility`, `compute-budget` | que dos corridas con la misma semilla y entorno den el mismo modelo |
| `evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` | umbrales por segmento; invariancia, dirección y funcionalidad mínima; **reejecución sobre el modelo vigente** |
| `serving` | `contract-compat`, `latency-p99`, `rollback-drill` | compatibilidad hacia atrás; p99 bajo la carga declarada; que la reversión funcione |
| `monitoring` | `alert-backtest`, `false-positive-budget` | que la alerta dispare en incidentes pasados y calle ante el ruido |
| `problem`, `governance` | `human-review` | revisión humana según el tier |

```bash
python gates/run.py --change <nombre>
```

Cada gate lee su criterio del bloque ` ```yaml contract ` del requisito correspondiente — nunca
lo lleva escrito dentro. Si el umbral vive en el código y no en la spec, la spec no gobierna nada.

## Cómo reportas

- Un gate en rojo **bloquea**. No lo presentes como advertencia menor ni lo justifiques.
- Reporta lo que falta, no solo lo que pasó. Un gate que no se pudo ejecutar no es un gate verde.
- Si un gate pasa pero **no podía fallar por construcción**, dilo: es teatro de gobernanza y vale
  como hallazgo.
- Métricas por segmento siempre que el delta toque `evaluation`.

## Lo que no haces

No arreglas el código para que pase. No ajustas el umbral para que entre — si el umbral está mal
calibrado, eso es otro change sobre `<modelo>-evaluation`, con su propia revisión.

Tu salida honesta vale más que tu salida verde.

Con todos los gates en verde, emite el comprobante con `sdd-receipt`.
