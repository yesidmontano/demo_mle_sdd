# demo_mle_sdd — MLOps gobernado por especificaciones

Demo de referencia del marco **SDD aplicado al ciclo de vida de ML**. Se monta sobre
[OpenSpec](https://github.com/Fission-AI/OpenSpec) —su CLI, su estructura y sus verbos— y le
añade la capa que ML necesita.

## La idea en una página

SDD nació para gobernar **código**, que cabe entero en un pull request. En ML el comportamiento
lo producen **tres artefactos** —código, datos y modelo entrenado— y solo uno pasa por revisión
de pares. Por eso aquí la especificación se extiende a los tres, bajo una regla dura:

> **Toda spec es ejecutable.** Si un requisito no desciende a un contrato comprobable y de ahí a
> un gate con capacidad de bloqueo, no gobierna nada: es documentación. Se marca `non_binding`.

### Dos ciclos ortogonales

- **Ciclo macro — ciclo de vida ML**: Negocio → Datos → Preparación → Modelado → Evaluación →
  Despliegue → **Operación y monitoreo**. Iterativo, no lineal, y no termina.
- **Ciclo micro — SDD**: explorar → proponer → implementar → verificar → sincronizar → archivar.

**SDD no es una fase del ciclo de vida.** Cada fase macro contiene N *changes* y cada uno recorre
el ciclo SDD completo. No todo change despliega: un análisis archiva un hallazgo; un experimento
fallido, un resultado negativo con su evidencia.

## Estructura

```
openspec/
  config.yaml                          tiers, gate_routing y rules por fase
  specs/<modelo>-<aspecto>/spec.md     main specs — el Spec Pack vigente
  changes/<change>/
    proposal.md  design.md  tasks.md
    specs/<modelo>-<aspecto>/spec.md   delta specs (ADDED/MODIFIED/REMOVED/RENAMED)
    evidence/                          seal.json · receipt.json · salidas de gates
  changes/archive/                     changes cerrados
gates/                                 los contratos, ejecutables
.agents/                               subagentes de fase
.claude/skills/                        el flujo SDD-MLOps
.claude/hooks/                         lo que el entorno impone, fuera del control del agente
```

### Los ocho aspectos

Una capability se nombra `<modelo>-<aspecto>`. El Spec Pack de un modelo es el conjunto que
comparte prefijo.

`problem` · `data` · `features` · `training` · `evaluation` · `serving` · `monitoring` ·
`governance`

### Por qué markdown con un bloque `yaml contract`

El formato de requisitos y escenarios es el de OpenSpec, así que `openspec validate`, la
sincronización y el archivado funcionan sin adaptaciones. Pero un requisito en prosa no puede
fallar, así que cada uno lleva dentro un bloque ` ```yaml contract ` con su umbral, esquema o
invariante. El escenario lo lee una persona; el bloque lo ejecuta un gate.

## Reglas del repositorio

1. **Ninguna feature edita `openspec/specs/` directamente.** Escribe delta specs en el change; la
   fusión ocurre al sincronizar o archivar, y solo con comprobante. Un hook lo impone.
2. **Los gates se derivan del aspecto de las capabilities que toca el delta**, no de la fase del
   ciclo de vida:

   | Aspecto | Gates |
   |---|---|
   | `data` | `data-contract`, `freshness` |
   | `features` | `train-serve-parity`, `leakage-check` |
   | `training` | `reproducibility`, `compute-budget` |
   | `evaluation` | `slice-eval`, `behavioral-tests`, `incumbent-rerun` |
   | `serving` | `contract-compat`, `latency-p99`, `rollback-drill` |
   | `monitoring` | `alert-backtest`, `false-positive-budget` |
   | `problem`, `governance` | `human-review` |

3. **Congelar antes de leer.** El candidato se sella y solo entonces se evalúa, de modo que la
   evidencia pertenece a la versión exacta que se promueve.
4. **Proporcionalidad.** Un change de alcance reducido recorre la vía abreviada. El tier fija el
   corte. Imponer el ciclo completo a todo el trabajo es el modo de fallo característico de estos
   marcos.
5. **El comprobante es el objeto de promoción**, no un permiso. Liga cinco identidades:
   `spec_pack + dataset + código + entorno + modelo`.

## Flujo de trabajo

| Quiero… | Skill | Equivalente OpenSpec |
|---|---|---|
| Investigar datos o viabilidad | `sdd-explore` | `openspec-explore` |
| Crear o revisar las main specs de un modelo | `sdd-spec-pack` | — (capa ML) |
| Abrir un change con sus artefactos | `sdd-propose` | `openspec-propose` |
| Implementar las tareas y sellar | `sdd-apply` | `openspec-apply-change` |
| Correr los gates que activa el alcance | `sdd-verify` | — (capa ML) |
| Emitir el comprobante | `sdd-receipt` | — (capa ML) |
| Fusionar deltas a main specs | `sdd-sync-specs` | `openspec-sync-specs` |
| Cerrar el change | `sdd-archive` | `openspec-archive-change` |

Los tres skills sin equivalente son exactamente lo que ML añade: el artefacto gobernado no se
revisa leyéndolo, hay que medirlo, y "la misma versión" no la define el commit.

Los subagentes de `.agents/` cubren cada fase. Regla de separación: **el subagente que implementa
no es el que aprueba.** `apply` y `verify` nunca comparten contexto.

## Convenciones de código

- Python 3.11+. Dependencias con `uv` si está disponible, si no `pip` en un venv local.
- Los gates viven en `gates/` y son ejecutables independientes: entran por CLI, salen con
  código 0 (pasa) o distinto de 0 (bloquea) y un JSON en stdout.
- Nada de notebooks en el flujo gobernado. La exploración vive en un change y su conclusión se
  archiva como hallazgo.
