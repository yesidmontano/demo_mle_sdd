"""El guard de pasos debe poder bloquear, y debe fallar en abierto ante la duda."""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / ".claude/hooks/sdd_phase_guard.py"


def run(cwd: Path, subagent: str, prompt: str, tool: str = "Agent") -> subprocess.CompletedProcess:
    event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"subagent_type": subagent, "prompt": prompt}}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), text=True, capture_output=True, cwd=cwd)


def make_change(root: Path, name: str, aspects=(), files=()):
    d = root / "openspec/changes" / name
    for a in aspects:
        (d / "specs" / f"modelo-{a}").mkdir(parents=True)
    for f in files:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("x")
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_apply_and_verify_need_tasks(tmp_path):
    make_change(tmp_path, "c1")
    for phase in ("opsx-apply", "opsx-verify"):
        r = run(tmp_path, phase, "Implementa openspec/changes/c1")
        assert r.returncode == 2 and "tasks.md" in r.stderr
    make_change(tmp_path, "c2", files=["tasks.md"])
    assert run(tmp_path, "opsx-apply", "openspec/changes/c2").returncode == 0


def test_verify_of_evaluation_change_needs_a_seal(tmp_path):
    make_change(tmp_path, "c3", aspects=["evaluation"], files=["tasks.md"])
    r = run(tmp_path, "opsx-verify", "verifica --change c3")
    assert r.returncode == 2 and "seal.json" in r.stderr
    make_change(tmp_path, "c4", aspects=["evaluation"], files=["tasks.md", "evidence/seal.json"])
    assert run(tmp_path, "opsx-verify", "verifica --change c4").returncode == 0


def test_archive_of_serving_change_needs_a_receipt_but_others_do_not(tmp_path):
    make_change(tmp_path, "c5", aspects=["serving"], files=["tasks.md"])
    r = run(tmp_path, "opsx-archive", "archiva openspec/changes/c5")
    assert r.returncode == 2 and "receipt.json" in r.stderr
    make_change(tmp_path, "c6", aspects=["serving"], files=["tasks.md", "evidence/receipt.json"])
    assert run(tmp_path, "opsx-archive", "archiva openspec/changes/c6").returncode == 0
    make_change(tmp_path, "c7", aspects=["data"], files=["tasks.md"])                # no promueve modelo
    assert run(tmp_path, "opsx-archive", "archiva openspec/changes/c7").returncode == 0


def test_guard_fails_open(tmp_path):
    make_change(tmp_path, "c8")
    assert run(tmp_path, "otro-agente", "openspec/changes/c8").returncode == 0        # no es opsx-*
    assert run(tmp_path, "opsx-apply", "sin ningún change nombrado").returncode == 0  # sin change identificable
    assert run(tmp_path, "opsx-apply", "openspec/changes/no-existe").returncode == 0  # change inexistente/archivado
    assert run(tmp_path, "opsx-propose", "openspec/changes/c8").returncode == 0       # propose no tiene precondición
    assert run(tmp_path, "opsx-apply", "openspec/changes/c8", tool="Bash").returncode == 0
    broken = subprocess.run([sys.executable, str(HOOK)], input="{no es json", text=True, capture_output=True, cwd=tmp_path)
    assert broken.returncode == 0
