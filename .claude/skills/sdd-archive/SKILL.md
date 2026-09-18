---
name: sdd-archive
description: Cerrar un change — fusionar sus deltas y moverlo al archivo. Usar cuando los gates pasan, y también cuando el change termina sin despliegue (un hallazgo o un resultado negativo).
---

# Archivar — `openspec-archive-change` con comprobante

Cierra el change y actualiza las main specs. Usa el CLI:

```bash
openspec archive <nombre>
```

## Precondición innegociable

Existe `evidence/receipt.json`, verificable, con todos los gates que el alcance activó en verde.
**Sin comprobante no hay fusión.** Un hook lo comprueba al entrar en la fase; si te piden
archivar sin él, di que no y explica qué falta.

Si los deltas ya se fusionaron con `sdd-sync-specs`, archiva sin volver a fusionarlos.

## Change que cambia el contrato

1. `python gates/receipt.py --change <nombre> --verify`
2. Comprobar que el `spec_pack` del comprobante coincide con `openspec/specs/`. Si divergió,
   rehacer la verificación; no forzar.
3. Fusionar (si falta) y mover a `openspec/changes/archive/<nombre>/` con la evidencia completa.
4. Registrar el comprobante en el índice de promociones.

## Change que no despliega

Un análisis exploratorio o un experimento fallido **archivan igual**, sin delta que fusionar:

1. `evidence/finding.md` con la conclusión y los datos que la sostienen.
2. Si el resultado es negativo, decir **qué se descarta y bajo qué condiciones**, para que nadie
   repita la investigación dentro de seis meses.
3. Mover a `openspec/changes/archive/<nombre>/`. Las main specs no cambian.

Esto no es burocracia añadida: es el trabajo que hoy se pierde en notebooks, recuperado sin
esfuerzo extra porque el flujo es el mismo para todo change.

## Lo que archivar NO significa

No despliega y no aprueba. Registra el estado real, incluido el trabajo inacabado si se archiva
explícitamente. La política del repositorio y el tier deciden quién firma; el comprobante informa.
