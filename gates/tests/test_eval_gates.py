"""Cada gate de evaluación debe poder fallar."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for d in ("gates", "code/05-evaluation", "code/03-data_preparation"):
    sys.path.insert(0, str(ROOT / d))
import behavioral_tests as bt
import preprocessing as pp
import seal
import slice_eval as se

CONTRACTS = [{"assert": [
    {"metric": "pr_auc", "scope": "global", "op": ">=", "relative_to_baseline": True, "tolerance": 0.0},
    {"metric": "pr_auc", "scope": "slice", "op": ">=", "relative_to_baseline": True, "tolerance": -0.02},
    {"metric": "ece", "scope": "global", "op": "<=", "value": 0.05},
]}]


def res(pr, ece, slice_pr):
    return {"global": {"pr_auc": pr, "ece": ece}, "slices": {"sales_channel": {"Mobile": {"pr_auc": slice_pr}}}}


def oks(checks):
    return [c["ok"] for c in checks]


def test_slice_eval_passes_when_candidate_is_better():
    assert all(oks(se.judge(res(0.40, 0.01, 0.30), res(0.35, 0.02, 0.28), CONTRACTS)))


def test_slice_eval_fails_on_global_slice_and_calibration():
    base = res(0.35, 0.02, 0.30)
    assert not all(oks(se.judge(res(0.30, 0.01, 0.30), base, CONTRACTS)))    # global peor
    assert not all(oks(se.judge(res(0.40, 0.01, 0.20), base, CONTRACTS)))    # un segmento retrocede > 0.02
    assert not all(oks(se.judge(res(0.40, 0.09, 0.30), base, CONTRACTS)))    # mal calibrado
    assert all(oks(se.judge(res(0.40, 0.01, 0.29), base, CONTRACTS)))        # retroceso dentro de la tolerancia


class Fake:
    """Modelo de juguete: `mode` decide cómo se porta."""
    def __init__(self, mode):
        self.mode = mode

    def predict_proba(self, x):
        n = len(x)
        if self.mode == "invalid":
            return np.full((n, 2), 1.5)
        if self.mode == "crash_on_unseen" and (x["booking_origin"] == "Atlantis").any():
            raise ValueError("categoría no vista")
        base = 0.2 + 0.1 * (x[pp.WANTS].sum(axis=1).to_numpy() if self.mode != "reverse" else -x[pp.WANTS].sum(axis=1).to_numpy())
        p = np.clip(base, 0.01, 0.99)
        return np.column_stack([1 - p, p])


def raw():
    r = np.random.default_rng(0)
    df = pd.DataFrame({c: r.integers(0, 2, 300) for c in pp.WANTS})
    for c in pp.INPUT_COLUMNS:
        if c not in df:
            df[c] = "x"
    return df


TESTS = {"probabilities_valid": 0.0, "unseen_category_tolerated": 0.0, "wants_flags_directional": 0.0}


def test_behavioral_passes_on_sane_model():
    assert all(oks(bt.run_tests(Fake("ok"), raw(), TESTS)))


def test_behavioral_fails_on_invalid_probs_crash_and_wrong_direction():
    assert not bt.run_tests(Fake("invalid"), raw(), TESTS)[0]["ok"]
    assert not bt.run_tests(Fake("crash_on_unseen"), raw(), TESTS)[1]["ok"]
    assert not bt.run_tests(Fake("reverse"), raw(), TESTS)[2]["ok"]


def test_seal_refuses_to_overwrite(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    ev = tmp_path / "openspec/changes/c/evidence"
    ev.mkdir(parents=True)
    (ev / "seal.json").write_text("{}")
    monkeypatch.setattr(sys, "argv", ["seal.py", "--change", "c", "--run-id", "r", "--baseline-run-id", "b"])
    assert seal.main() == 1
    assert json.loads(capsys.readouterr().out)["status"] == "fail"
    assert (ev / "seal.json").read_text() == "{}"


def test_incumbent_rerun_fails_when_baseline_does_not_reproduce():
    sys.path.insert(0, str(ROOT / "code/04-modeling"))
    import incumbent_rerun as ir
    contract = {"assert": [{"metric": "log_loss_abs_diff", "op": "<=", "value": 1e-6}]}
    assert ir.evaluate(0.3634, 0.3634, contract)[0]["ok"]
    assert not ir.evaluate(0.3634, 0.3700, contract)[0]["ok"]
