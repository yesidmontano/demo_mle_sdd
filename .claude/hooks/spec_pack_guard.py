#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit) — veta la escritura directa sobre el Spec Pack.

Alcance deliberadamente estrecho: SOLO escrituras de archivo cuya ruta cae bajo
openspec/specs/. No mira comandos de shell, ni git, ni configuracion del repo.
Falla en ABIERTO antcualquier error.

Escotilla: SDD_ARCHIVE=1, que es lo que usa gates/merge.py al fusionar.
"""
import json, os, sys

GUARDED = os.path.join("openspec", "specs")

def main() -> int:
    if os.environ.get("SDD_ARCHIVE") == "1":
        return 0
    try:
        e = json.load(sys.stdin)
    except Exception:
        return 0
    if e.get("tool_name") not in {"Write", "Edit", "MultiEdit"}:
        return 0
    p = (e.get("tool_input") or {}).get("file_path") or ""
    if GUARDED not in os.path.normpath(p):
        return 0
    sys.stderr.write(
        "BLOQUEADO: openspec/specs/ es el Spec Pack vigente y refleja lo que esta en produccion.\n\n"
        "Ninguna feature lo edita directamente. Escribe un delta en\n"
        "openspec/changes/<feature-id>/spec.delta.yaml declarando `touches` (skill: sdd-delta).\n"
        "La fusion ocurre al archivar, via gates/merge.py.\n"
    )
    return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
