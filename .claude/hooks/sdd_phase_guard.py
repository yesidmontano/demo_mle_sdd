#!/usr/bin/env python3
"""PreToolUse(Agent) — precondiciones de fase SDD.

Se activa SOLO al despachar un subagente `sdd-*`. Cualquier otra herramienta,
cualquier otro subagente y cualquier duda: no-op. El guard gobierna la entrada
a una fase, no las operaciones de archivo ni la shell.

Falla en ABIERTO: si no puede determinar el contexto, permite. Un guard que se
rompe no debe convertirse en un bloqueo del repositorio.
"""
import json, os, re, sys

# fase -> (archivo que debe existir bajo changes/<id>/, explicación)
PRECONDITIONS = {
    "sdd-apply":      ("tasks.md",              "el change no tiene tasks.md: genera los artefactos antes de implementar (skill: sdd-tasks)"),
    "sdd-verify":     ("evidence/seal.json",    "el candidato no esta sellado: congela antes de leer (`python gates/seal.py`)"),
    "sdd-archive":    ("evidence/receipt.json", "no hay comprobante valido: sin comprobante no hay fusion (skill: sdd-verify)"),
}

def main() -> int:
    try:
        e = json.load(sys.stdin)
    except Exception:
        return 0
    if e.get("hook_event_name") != "PreToolUse" or e.get("tool_name") != "Agent":
        return 0
    ti = e.get("tool_input") or {}
    phase = (ti.get("subagent_type") or "").strip()
    if phase not in PRECONDITIONS:
        return 0
    m = re.search(r"changes/([A-Za-z0-9._-]+)", str(ti.get("prompt", "")))
    if not m:
        return 0  # sin feature identificable: no es asunto del guard
    fid = m.group(1)
    needed, why = PRECONDITIONS[phase]
    path = os.path.join("openspec", "changes", fid, needed)
    if os.path.exists(path):
        return 0
    sys.stderr.write(
        f"BLOQUEADO: la fase {phase} exige {path}, que no existe.\n\n{why}\n"
    )
    return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail-open, siempre
