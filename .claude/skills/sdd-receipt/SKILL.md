---
name: sdd-receipt
description: Sellar el candidato y emitir el comprobante de promoción que liga spec, datos, código, entorno y modelo. Usar después de entrenar y antes de sincronizar o archivar.
---

# Comprobante — lo que OpenSpec resuelve con un commit

En software la versión la identifica el commit. En ML no: el mismo código sobre otro snapshot de
datos produce otro modelo, y el mismo modelo en otro entorno produce otras predicciones. **"La
misma versión" solo queda definida por cinco identidades juntas.**

## Congelar antes de leer

El orden importa y es el punto entero del mecanismo: el candidato se sella primero, y **solo
entonces** se evalúa. Invertirlo produce un comprobante que describe algo que ya no existe.

```bash
python gates/seal.py --change <nombre>     # ANTES de mirar ninguna métrica
```

| Identidad | Qué cubre |
|---|---|
| `spec_pack` | hash de las main specs vigentes del modelo + del delta aplicado |
| `dataset` | hash del snapshot exacto, no de la consulta |
| `code` | commit del árbol de trabajo, limpio |
| `env` | lockfile de dependencias resuelto |
| `model` | hash del artefacto entrenado |

Si el árbol está sucio, el sellado falla. Un candidato no reproducible no se promueve.

## Emitir

```bash
python gates/receipt.py --change <nombre>            # emite evidence/receipt.json
python gates/receipt.py --change <nombre> --verify   # lo valida
```

El comprobante lleva las cinco identidades, el resultado de cada gate activado, las métricas por
segmento, el timestamp y el aprobador cuando el tier lo exige.

## Qué se sigue

- **La promoción es una máquina de estados sobre comprobantes**, no un permiso. Exige que el
  `spec_pack` del comprobante coincida con las main specs vigentes.
- **La auditoría es una consulta, no una investigación.**
- **La reversión es determinista**: el comprobante anterior describe el estado de destino.
- El comprobante **informa** la entrega; no la sustituye. Quién firma sigue siendo política de la
  organización y del tier.

`sdd-sync-specs` y `sdd-archive` lo exigen como precondición, y un hook lo comprueba.
