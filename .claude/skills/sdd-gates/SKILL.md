---
name: sdd-gates
description: Determinar y ejecutar los gates que aplican a una feature según el alcance de su delta. Usar antes de dar por buena cualquier feature, y al escribir un gate nuevo en gates/.
---

# Gates — enrutamiento por alcance del delta

**La regla que hace mecánico al marco:** los gates aplicables se derivan de **qué documentos del
Spec Pack toca el delta** (`touches`), no de la fase del ciclo de vida en que la feature se sitúa.

## Procedimiento

1. **Leer `touches`** de `openspec/changes/<feature-id>/spec.delta.yaml`.

2. **Resolver los gates** contra `openspec/config.yaml` → `gate_routing`:

   | `touches` | Gates | Qué comprueban |
   |---|---|---|
   | `10-data` | `data-contract`, `freshness` | Esquema, tipos, rangos, nulabilidad, unicidad, retraso máximo |
   | `20-features` | `train-serve-parity`, `leakage-check` | Que la misma definición produzca el mismo valor offline y online; que ninguna columna prohibida ni información futura entre al entrenamiento |
   | `30-training` | `reproducibility`, `compute-budget` | Que dos corridas con la misma semilla y entorno den el mismo modelo; que el coste no se dispare |
   | `40-evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` | Umbrales por segmento; invariancia, dirección y funcionalidad mínima; **reejecución sobre el modelo vigente** |
   | `50-serving` | `contract-compat`, `latency-p99`, `rollback-drill` | Compatibilidad hacia atrás del esquema; p99 bajo la carga declarada; que la reversión funcione de verdad |
   | `60-monitoring` | `alert-backtest`, `false-positive-budget` | Que la alerta dispare en incidentes pasados y calle ante el ruido |
   | `00-problem`, `70-governance` | `human-review` | Revisión humana según el tier |

3. **Ejecutar solo esos gates**:
   ```bash
   python gates/run.py --change <feature-id>
   ```
   Cada gate es un ejecutable independiente: entra por CLI, sale con código `0` (pasa) o
   distinto de `0` (bloquea), y escribe un JSON en stdout que va a `evidence/`.

4. **Interpretar el resultado sin suavizarlo.** Un gate en rojo bloquea; no se reporta como
   "advertencia menor". Si el gate está mal calibrado, eso es una feature sobre `40-evaluation`,
   no una razón para ignorarlo.

## Dos casos con trampa

- **`40-evaluation` exige `incumbent-rerun`**: un umbral nuevo se reejecuta sobre el modelo **ya
  en producción**. Sin esto, subir el listón invalidaría retroactivamente lo que ya está
  desplegado y nadie se enteraría.
- **`60-monitoring` exige `alert-backtest`**: la spec de monitoreo se redacta antes de ver el
  fenómeno que vigilará. Un umbral no se acepta por criterio del autor, sino porque dispara en
  los incidentes registrados y no en el ruido, con presupuesto de falsos positivos declarado.

## Escribir un gate nuevo

Va en `gates/<nombre>.py`, lee la cláusula correspondiente del Spec Pack y **falla de verdad**.
Un gate que no puede fallar es teatro de gobernanza: si al escribirlo no se encuentra un caso
que lo haga saltar, decirlo explícitamente en vez de dejarlo verde por construcción.

Instrumentar siempre dos números: *gate escape rate* (incidentes que ningún gate detectó) y
*false block rate*. Un gate que nunca bloquea no aporta información.
