---
name: sdd-spec-pack
description: Crear o revisar el Spec Pack de un modelo — los ocho documentos que forman su contrato vigente. Usar cuando nace un modelo nuevo, cuando hay que escribir specs de un modelo que ya está en producción, o cuando se revisa si una spec es realmente ejecutable.
---

# Spec Pack — el contrato vigente de un modelo

El Spec Pack es el **estado acumulado**: refleja lo que está en producción, no lo que se está
cambiando. Vive en `openspec/specs/<modelo>/` y su hash es la identidad del contrato.

## Cuándo se usa

- Nace un modelo → crear el pack desde `openspec/specs/_template/`.
- Hay un modelo ya desplegado y sin specs → **este es el primer paso del roadmap**: escribir el
  pack de lo que ya existe, sin automatizar nada todavía. Entrega una línea base auditable.
- Revisión de ejecutabilidad → auditar que cada cláusula pueda fallar.

## Procedimiento

1. **Determinar el tier** consultando `openspec/config.yaml` → `tiers`. El tier decide qué
   documentos son obligatorios. No todos los modelos pagan el pack completo.

2. **Copiar solo los documentos que el tier exige**:
   ```bash
   mkdir -p openspec/specs/<modelo>
   cp openspec/specs/_template/{00-problem,10-data,40-evaluation}.yaml openspec/specs/<modelo>/
   ```

3. **Rellenar en este orden**, porque cada uno restringe al siguiente:
   `00-problem` → `10-data` → `20-features` → `30-training` → `40-evaluation` →
   `50-serving` → `60-monitoring` → `70-governance`.

4. **Aplicar el test de ejecutabilidad a cada cláusula.** Preguntar, literalmente:
   *¿Qué comando haría fallar esto?* Si no hay respuesta, la cláusula no gobierna. Dos salidas
   legítimas: bajarla a un umbral/esquema/invariante, o marcarla `non_binding: true` para que
   nadie la confunda con una garantía. **Ninguna cláusula se queda en prosa sin marcar.**

5. **Verificar las tres coherencias que se rompen en silencio**:
   - `40-evaluation.slices` y `60-monitoring.watched_slices` deben nombrar **los mismos
     segmentos**. Si divergen, la evaluación offline y la vigilancia online miden objetos
     distintos.
   - Toda feature de `20-features` tiene `offline_source` **y** `online_source`.
   - `00-problem.ml_objective.link_to_business` está relleno: si nadie sabe traducir la métrica
     ML a la de negocio, el modelo no tiene criterio de éxito.

## Reglas

- Umbrales **relativos a la línea base vigente** siempre que sea posible. Un umbral absoluto
  envejece mal en un régimen no estacionario.
- `40-evaluation` exige umbrales **por segmento**, no solo agregados: un AUC global que sube
  puede ocultar degradación en un subconjunto, y es el modo de falla más común.
- Nunca editar `openspec/specs/` para introducir un cambio funcional. Eso es un delta; usar
  `sdd-delta`. Este skill solo crea el pack o corrige errores de transcripción de lo que YA
  está en producción.
