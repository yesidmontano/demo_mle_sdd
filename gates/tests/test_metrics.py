import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code" / "05-evaluation"))
import metrics as M


def test_captured_at_k_perfect_and_random():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert M.captured_conversions_at_k(y, y.astype(float), 0.2) == 1.0
    assert M.captured_conversions_at_k(y, np.zeros(10), 0.2) <= 1.0


def test_ece_perfect_and_worst():
    y = np.array([0, 0, 1, 1])
    assert M.ece(y, np.array([0.0, 0.0, 1.0, 1.0])) == 0
    assert M.ece(y, np.array([1.0, 1.0, 0.0, 0.0])) == pytest.approx(1.0)


def test_slice_metrics_skips_small_segments():
    r = np.random.default_rng(0)
    y, p = r.integers(0, 2, 1200), r.random(1200)
    s = pd.DataFrame({"g": ["a"] * 1000 + ["b"] * 200})
    out = M.slice_metrics(y, p, s, 0.2, min_size=500)
    assert list(out["g"]) == ["a"]
    assert "slice_g_a_pr_auc" in M.flat(out)
