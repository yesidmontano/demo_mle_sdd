#!/usr/bin/env python3
"""PreToolUse(Agent) — precondiciones de paso de un change de OpenSpec.

Se activa SOLO al despachar un subagente `opsx-*` (los que envuelven las skills `openspec-*`). Cualquier
otra herramienta, cualquier otro subagente y cualquier duda: no-op. El guard gobierna la entrada a un
paso, no las operaciones de archivo ni la shell.

Precondiciones (todas sobre el change que nombra el prompt):
  opsx-apply    tasks.md existe.
  opsx-verify   tasks.md existe; si el delta toca `evaluation`, evidence/seal.json existe
                (evaluar antes de sellar produce evidencia sobre algo que ya no existe).
  opsx-archive  si el delta toca `serving` (el change promueve un modelo), evidence/receipt.json existe.
                `openspec archive` corre por shell y no lo verifica: este guard es la única guardia.

Falla en ABIERTO: si no puede determinar el contexto, permite. Un guard que se rompe no debe convertirse
en un bloqueo del repositorio.
"""
import json
import os
import re
import sys

CHANGE_RE = re.compile(r"(?:changes/|--change[ =]|change[ `'\"]+)([A-Za-z0-9][A-Za-z0-9._-]*)")


def touches(change_dir: str, aspect: str) -> bool:
    specs = os.path.join(change_dir, "specs")
    return os.path.isdir(specs) and any(d.endswith(f"-{aspect}") for d in os.listdir(specs))


def missing(phase: str, change_dir: str):
    """(ruta que falta, explicación) o None si la precondición se cumple."""
    def need(rel: str, why: str):
        return None if os.path.exists(os.path.join(change_dir, rel)) else (rel, why)

    if phase in ("opsx-apply", "opsx-verify"):
        gap = need("tasks.md", "el change no tiene tasks.md: genera los artefactos antes (skill: openspec-propose)")
        if gap:
            return gap
    if phase == "opsx-verify" and touches(change_dir, "evaluation"):
        return need("evidence/seal.json", "el candidato no está sellado: congela antes de leer (`python gates/seal.py`, "
                                          "lo invoca code/04-modeling/train.py)")
    if phase == "opsx-archive" and touches(change_dir, "serving"):
        return need("evidence/receipt.json", "el change promueve un modelo y no hay comprobante válido: sin comprobante no "
                                             "hay fusión (`python gates/receipt.py --change <id> --version <N>`)")
    return None


def main() -> int:
    try:
        e = json.load(sys.stdin)
    except Exception:
        return 0
    if e.get("hook_event_name") != "PreToolUse" or e.get("tool_name") != "Agent":
        return 0
    ti = e.get("tool_input") or {}
    phase = (ti.get("subagent_type") or "").strip()
    if not phase.startswith("opsx-"):
        return 0
    m = CHANGE_RE.search(str(ti.get("prompt", "")))
    if not m or m.group(1) == "archive":
        return 0  # sin change identificable: no es asunto del guard
    change_dir = os.path.join("openspec", "changes", m.group(1))
    if not os.path.isdir(change_dir):
        return 0  # change inexistente o ya archivado
    gap = missing(phase, change_dir)
    if gap is None:
        return 0
    path, why = os.path.join(change_dir, gap[0]), gap[1]
    sys.stderr.write(f"BLOQUEADO: el paso {phase} exige {path}, que no existe.\n\n{why}\n")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail-open, siempre
