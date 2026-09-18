---
name: sdd-delta
description: Abrir una feature como delta contra el Spec Pack — propuesta, spec delta, diseño y tareas. Usar al empezar cualquier unidad de trabajo: un análisis, un experimento, una fuente de datos nueva, un umbral nuevo o un cambio de contrato de servicio.
---

# Delta — una feature en vuelo

Una **feature** es cualquier unidad de cambio, esté en la fase del ciclo de vida que esté. No
solo una funcionalidad: también un análisis de calidad de una fuente, un experimento de
arquitectura, un segmento crítico nuevo o un cambio de contrato de API.

**Ninguna feature edita `openspec/specs/` directamente.** Escribe un delta; la fusión ocurre solo
al archivar. Un hook del entorno lo impone, así que no es una convención opcional.

## Procedimiento

1. **Nombrar la feature** en kebab-case y crear su carpeta:
   ```bash
   mkdir -p openspec/changes/<feature-id>/evidence
   ```

2. **Decidir la vía** según el tier del modelo (`openspec/config.yaml` → `tiers`):
   - **Vía abreviada** (tier 3, o cambio pequeño y entendido): `proposal.md` + `evidence/`.
     Sin `design.md` ni `tasks.md`. Imponer el ciclo completo a todo el trabajo es lo que mata
     estos marcos.
   - **Ciclo completo**: los cuatro artefactos.

3. **`proposal.md`** — intención, alcance, enfoque. Responde:
   - ¿Qué problema resuelve y para quién?
   - ¿Qué NO entra en el alcance?
   - ¿Qué alternativa se descarta y por qué?

4. **`spec.delta.yaml`** — **qué cambia del Spec Pack**, no el pack entero:
   ```yaml
   model: <modelo>
   touches: ["40-evaluation"]        # <- esto decide los gates. Ser exacto.
   rationale: "<por qué el contrato debe cambiar>"
   changes:
     - doc: 40-evaluation
       op: add                        # add | modify | remove
       path: slices
       value:
         - name: rutas-alta-demanda
           filter: "demand_tier == 'high'"
           thresholds: [{ metric: MAE, op: "<=", value: 0.0, relative_to_baseline: true }]
           min_support: 100
   ```
   `touches` es el campo más importante del archivo: **el enrutamiento de gates se deriva de él.**
   Declararlo de menos es saltarse verificaciones; de más, pagar gates que no aplican.

5. **`design.md`** (ciclo completo) — decisiones de arquitectura con su alternativa descartada.
   Batch vs online, stateless vs stateful, build vs buy.

6. **`tasks.md`** (ciclo completo) — checklist ordenada donde **cada tarea deja un artefacto
   verificable**, no una afirmación de que algo se hizo.

## Features que no despliegan

Un análisis exploratorio y un experimento fallido **también son features y también archivan**.
Su delta lleva `touches: []` y su `evidence/` contiene el hallazgo o el resultado negativo. Esto
es deliberado: es el trabajo que hoy se evapora en notebooks y se repite meses después.

## Siguiente paso

Con el delta escrito, usar `sdd-gates` para saber qué verificaciones activa su alcance.
