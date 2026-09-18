---
name: sdd-archive
description: Cerrar una feature — fusionar su delta al Spec Pack y archivar la evidencia. Usar cuando los gates pasan, y también cuando la feature termina sin despliegue (un hallazgo o un resultado negativo).
---

# Archivar — fusión y cierre

Archivar hace dos cosas: **fusiona el delta al Spec Pack** y **preserva la evidencia**. El Spec
Pack pasa a reflejar el nuevo estado de producción.

## Precondición

Existe `openspec/changes/<feature-id>/evidence/receipt.json`, válido, con todos los gates que el
alcance activó en verde. **Sin comprobante no hay fusión.** Un hook del entorno lo impone.

## Procedimiento — feature que cambia el contrato

1. Verificar el comprobante:
   ```bash
   python gates/receipt.py --change <feature-id> --verify
   ```
2. Comprobar que `spec_pack` del comprobante coincide con el estado actual de
   `openspec/specs/<modelo>/`. Si alguien fusionó otra feature entretanto, el comprobante quedó
   obsoleto: **rehacer la evaluación sobre el pack nuevo**, no forzar la fusión.
3. Aplicar el delta:
   ```bash
   python gates/merge.py --change <feature-id>
   ```
4. Mover la feature a `openspec/changes/_archived/<feature-id>/` con su evidencia completa.
5. Registrar el comprobante en el índice de promociones.

## Procedimiento — feature que NO despliega

Un análisis exploratorio o un experimento fallido **archivan igual**, con `touches: []`:

1. Escribir `evidence/finding.md` con la conclusión y los datos que la sostienen.
2. Si el resultado es negativo, decir **qué se descarta y bajo qué condiciones**, para que nadie
   repita la investigación dentro de seis meses.
3. Mover a `openspec/changes/_archived/<feature-id>/`. No hay fusión: el Spec Pack no cambia.

Esto no es burocracia añadida: es exactamente el trabajo que hoy se pierde en notebooks, y se
recupera sin esfuerzo extra porque el flujo es el mismo para toda feature.

## Qué no hace archivar

Archivar **no despliega ni aprueba**. Registra el estado real, incluido el trabajo inacabado si
se archiva explícitamente. La política del repositorio y el tier siguen decidiendo quién firma
la entrega.
