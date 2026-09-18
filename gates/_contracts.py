"""Lee los bloques ```yaml contract``` de los delta specs de un change."""
import json
import operator
import re
import sys
from pathlib import Path

import yaml

BLOCK = re.compile(r"```yaml contract\n(.*?)```", re.S)
OPS = {"==": operator.eq, "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge}


def load(change: str, gate: str) -> list[dict]:
    """Contratos vinculantes del change que declaran `gate`. Sin `non_binding`."""
    out = []
    for spec in sorted(Path("openspec/changes", change, "specs").glob("*/spec.md")):
        for raw in BLOCK.findall(spec.read_text(encoding="utf-8")):
            c = yaml.safe_load(raw)
            if c.get("gate") == gate and not c.get("non_binding"):
                out.append(c)
    return out


def compare(value, op: str, expected) -> bool:
    if op == "between":
        return expected[0] <= value <= expected[1]
    return OPS[op](value, expected)


def finish(gate: str, change: str, checks: list[dict]) -> int:
    """Escribe evidence/<gate>.json, imprime el JSON y devuelve el código de salida."""
    if not checks:
        checks = [{"check": "contracts_found", "ok": False, "detail": "ningún contrato vinculante"}]
    status = "pass" if all(c["ok"] for c in checks) else "fail"
    result = {"gate": gate, "status": status, "metrics": checks,
              "detail": f"{sum(not c['ok'] for c in checks)} de {len(checks)} comprobaciones fallan"}
    if Path("openspec/changes", change).is_dir():
        ev = Path("openspec/changes", change, "evidence")
        ev.mkdir(exist_ok=True)
        (ev / f"{gate}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if status == "pass" else 1


def main_args(argv=None):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--change", required=True)
    p.add_argument("--model", default="conversion-sesion")
    return p.parse_args(argv)


def load_specs(gate: str, capability: str | None = None) -> list[dict]:
    """Contratos vinculantes de las main specs (`openspec/specs/`), para gates de changes ya archivados."""
    out = []
    pattern = f"{capability}/spec.md" if capability else "*/spec.md"
    for spec in sorted(Path("openspec/specs").glob(pattern)):
        for raw in BLOCK.findall(spec.read_text(encoding="utf-8")):
            c = yaml.safe_load(raw)
            if c.get("gate") == gate and not c.get("non_binding"):
                out.append(c)
    return out


def load_any(change: str, gate: str) -> list[dict]:
    """Contratos del change si sigue activo; si ya se archivó, los de las main specs vigentes."""
    return load(change, gate) or load_specs(gate)
