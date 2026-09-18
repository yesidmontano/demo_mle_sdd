---
name: sdd-spec-pack
description: Crear o revisar las main specs de un modelo — las ocho capabilities que forman su contrato vigente. Usar cuando nace un modelo, cuando hay que escribir specs de uno que ya está en producción, o cuando se audita si una spec puede realmente fallar.
---

# Spec Pack — las main specs de un modelo

El Spec Pack de un modelo es el conjunto de capabilities bajo `openspec/specs/` que comparten su
prefijo: `<modelo>-problem`, `<modelo>-data`, … Refleja **lo que está en producción**, no lo que
se está cambiando.

Ninguna feature lo edita: se escribe un delta en un change y la fusión ocurre en
`sdd-sync-specs` o `sdd-archive`. Un hook lo impone.

## Cuándo se usa

- **Nace un modelo** → crear las capabilities que el tier exige.
- **Hay un modelo ya desplegado y sin specs** → este es el primer paso del roadmap: escribir el
  contrato de lo que ya existe, sin automatizar nada. Entrega una línea base auditable.
- **Auditoría de ejecutabilidad** → comprobar que cada requisito puede fallar.

## Procedimiento

1. **Determinar el tier** en `openspec/config.yaml` → `tiers`. Decide qué aspectos son
   obligatorios. No todos los modelos pagan las ocho capabilities.

2. **Crear una capability por aspecto**, partiendo de la plantilla:
   ```bash
   mkdir -p openspec/specs/<modelo>-data
   cp openspec/templates/capability.spec.md openspec/specs/<modelo>-data/spec.md
   ```

3. **Rellenar en este orden**, porque cada aspecto restringe al siguiente:
   `problem` → `data` → `features` → `training` → `evaluation` → `serving` → `monitoring` →
   `governance`.

4. **Escribir cada requisito en dos capas.** El escenario lo lee una persona; el bloque
   ` ```yaml contract ` lo ejecuta un gate:

   ~~~markdown
   ### Requirement: Frescura del snapshot de tarifas

   El sistema SHALL rechazar un snapshot con más de 24 h de retraso.

   #### Scenario: Snapshot obsoleto

   - **WHEN** el snapshot más reciente tiene 30 h
   - **THEN** el gate de datos bloquea el entrenamiento

   ```yaml contract
   gate: freshness
   assert:
     - max_lag: 24h
       on_violation: block
   ```
   ~~~

5. **Aplicar el test de ejecutabilidad a cada requisito.** Pregunta, literalmente: *¿qué comando
   haría fallar esto?* Si no hay respuesta, dos salidas legítimas: bajarlo a un umbral, esquema o
   invariante, o marcarlo `non_binding: true` dentro del bloque. **Ningún requisito se queda en
   prosa sin marcar**, porque una spec que no puede fallar no gobierna nada.

6. **Verificar las tres coherencias que se rompen en silencio**:
   - Los slices de `<modelo>-evaluation` y los de `<modelo>-monitoring` nombran **los mismos
     segmentos**. Si divergen, la evaluación offline y la vigilancia online miden objetos
     distintos.
   - Toda feature de `<modelo>-features` declara fuente offline **y** online.
   - `<modelo>-problem` dice cómo se traduce la métrica de ML a la de negocio. Sin eso, el modelo
     no tiene criterio de éxito.

7. **Validar con el CLI**:
   ```bash
   openspec validate --specs
   ```

## Regla

Umbrales **relativos a la línea base vigente** siempre que sea posible: un umbral absoluto
envejece mal en un régimen no estacionario. Y en `evaluation`, umbrales **por slice**, no solo
agregados — un agregado que sube puede ocultar degradación en un subconjunto, y es el modo de
falla más común y más caro.
