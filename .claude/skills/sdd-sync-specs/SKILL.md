---
name: sdd-sync-specs
description: Fusionar los delta specs de un change a las main specs sin archivarlo. Usar cuando el contrato ya debe reflejar el cambio pero el trabajo continúa.
---

# Sincronizar — `openspec-sync-specs` con comprobante

Operación dirigida por el agente, igual que `openspec-sync-specs`: se leen los delta specs y se
editan las main specs directamente, lo que permite fusionar con criterio (añadir un escenario sin
copiar el requisito entero).

## Lo único que este skill añade

**No se sincroniza sin comprobante.** OpenSpec fusiona cuando el autor lo decide; aquí la fusión
exige `evidence/receipt.json` válido, porque las main specs describen lo que está en producción y
un contrato sin evidencia detrás es una afirmación.

```bash
python gates/receipt.py --change <nombre> --verify
```

## Procedimiento

1. `openspec status --change <nombre> --json` → toma los delta specs de
   `artifactPaths.specs.existingOutputPaths`. No asumas rutas.
2. Verifica el comprobante. Sin él, para.
3. Comprueba que el `spec_pack` del comprobante **coincide con el estado actual** de
   `openspec/specs/`. Si alguien sincronizó otra cosa entretanto, el comprobante quedó obsoleto:
   **rehacer la verificación sobre las specs nuevas**, no forzar la fusión.
4. Aplica cada delta a `openspec/specs/<capability>/spec.md`:
   - **ADDED** → si el requisito no existe, añadirlo; si existe, tratarlo como MODIFIED.
   - **MODIFIED** → aplicar el cambio preservando los escenarios no mencionados.
   - **REMOVED** → quitar el bloque entero del requisito.
   - **RENAMED** → renombrar de FROM a TO.
   - Si la capability no existe todavía, créala con su sección `## Purpose` y los requisitos.
5. **Conserva el bloque ` ```yaml contract ` de cada requisito.** Es lo que hace ejecutable a la
   spec; perderlo en la fusión la degrada a documentación sin que nadie lo note.

La escritura va por `gates/merge.py`, que es el único punto que habilita la escotilla del hook
sobre `openspec/specs/`.

## Resumen final

Qué capabilities se actualizaron y qué cambió en cada una (requisitos añadidos, modificados,
eliminados o renombrados).
