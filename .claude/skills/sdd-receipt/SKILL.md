---
name: sdd-receipt
description: Sellar el candidato y emitir el comprobante de promoción. Usar antes de evaluar un modelo entrenado y antes de cualquier promoción a producción.
---

# Comprobante — lo que reemplaza a la aprobación manual

Hoy la promoción es un acto de confianza. Aquí es un **objeto verificable**.

## Congelar antes de leer

El orden importa y es el punto entero del mecanismo: **el candidato se sella primero, y solo
entonces se evalúa.** Así la evidencia pertenece a la versión exacta que se promueve, y no a lo
que el workspace tenía un minuto después.

Invertir el orden —evaluar y luego sellar— produce un comprobante que describe algo que ya no
existe. Es el fallo más fácil de cometer y el más difícil de detectar después.

## Procedimiento

1. **Sellar**, antes de ejecutar ninguna evaluación:
   ```bash
   python gates/seal.py --change <feature-id>
   ```
   Calcula y congela las cinco identidades:

   | Identidad | Qué cubre |
   |---|---|
   | `spec_pack` | hash del contrato vigente + del delta aplicado |
   | `dataset` | hash del snapshot exacto usado, no de la consulta |
   | `code` | commit del árbol de trabajo, limpio |
   | `env` | lockfile de dependencias resuelto |
   | `model` | hash del artefacto entrenado |

   Si el árbol de trabajo está sucio, el sellado **falla**. Un candidato no reproducible no se
   promueve.

2. **Evaluar** con `sdd-gates`. Los resultados se escriben en
   `openspec/changes/<feature-id>/evidence/`.

3. **Emitir el comprobante**:
   ```bash
   python gates/receipt.py --change <feature-id>
   ```
   Produce `evidence/receipt.json` con las cinco identidades, el resultado de cada gate
   activado, las métricas por segmento, el timestamp y el aprobador cuando el tier lo exige.

## Qué se sigue de tener el comprobante

- **La promoción es una máquina de estados sobre comprobantes**, no un permiso. `Staging →
  Production` exige un comprobante válido cuyo `spec_pack` coincida con la spec vigente en la
  rama principal.
- **La auditoría es una consulta, no una investigación.** Pasa de días a minutos.
- **La reversión es determinista**: el comprobante anterior describe por completo el estado al
  que se vuelve.
- El comprobante **informa** la decisión de entrega; **no la sustituye**. Quién firma sigue
  siendo política de la organización y del tier, no del sistema.

## Por qué cinco hashes y no el commit

En software, el commit identifica la versión. En ML no: el mismo código sobre otro snapshot de
datos produce otro modelo, y el mismo modelo sobre otro entorno produce otras predicciones.
"La misma versión" solo queda definida por las cinco identidades juntas.
