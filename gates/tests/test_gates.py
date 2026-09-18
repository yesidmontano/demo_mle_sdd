"""Cada gate debe poder fallar: un gate que no falla no es un gate."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "gates"))
import data_contract as dc
import leakage_check as lc

CONTRACT = {"assert": [
    {"metric": "null_count", "op": "==", "value": 0},
    {"metric": "duplicate_rows", "op": "==", "value": 0},
    {"metric": "positive_rate", "op": "between", "value": [0.12, 0.18]},
    {"column": "num_passengers", "range": [1, 9]},
    {"column": "sales_channel", "values": ["Internet", "Mobile"]},
]}


def frame(n=1000, seed=0):
    r = np.random.default_rng(seed)
    return pd.DataFrame({"num_passengers": r.integers(1, 5, n),
                         "sales_channel": r.choice(["Internet", "Mobile"], n),
                         "noise": r.normal(size=n) + np.arange(n) * 1e-6,
                         "booking_complete": (np.arange(n) % 7 == 0).astype(int)})


def ok(checks):
    return all(c["ok"] for c in checks)


def test_data_contract_passes_on_valid_frame():
    assert ok(dc.evaluate(frame(), CONTRACT))


def test_data_contract_fails_on_null_duplicate_range_value():
    assert not ok(dc.evaluate(frame().assign(noise=lambda d: d.noise.where(d.index > 0)), CONTRACT))
    assert not ok(dc.evaluate(pd.concat([frame(), frame().head(1)]), CONTRACT))
    assert not ok(dc.evaluate(frame().assign(num_passengers=12), CONTRACT))
    assert not ok(dc.evaluate(frame().assign(sales_channel="Fax"), CONTRACT))
    assert not ok(dc.evaluate(frame().assign(booking_complete=1), CONTRACT))


LEAK = {"assert": [
    {"metric": "single_feature_auc", "op": "<", "value": 0.85, "applies_to": "all_features"},
    {"metric": "forbidden_columns_present", "op": "==", "value": 0, "forbidden": ["booking_complete_copy"]},
]}


def test_leakage_passes_on_noise():
    assert ok(lc.evaluate(frame(), LEAK))


def test_leakage_fails_on_leaky_feature_and_forbidden_column():
    df = frame()
    assert not ok(lc.evaluate(df.assign(leak=df.booking_complete * 5.0), LEAK))
    assert not ok(lc.evaluate(df.assign(booking_complete_copy=df.booking_complete), LEAK))


def test_cli_exits_nonzero_without_contracts(tmp_path):
    r = subprocess.run([sys.executable, "gates/data_contract.py", "--change", "no-existe"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 1
