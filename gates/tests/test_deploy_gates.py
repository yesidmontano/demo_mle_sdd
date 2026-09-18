"""Cada gate de serving y monitoring debe poder fallar."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for d in ("gates", "code/05-evaluation", "code/06-deploy", "code/07_operation_and_monitoring", "code/03-data_preparation"):
    sys.path.insert(0, str(ROOT / d))
import alert_backtest as ab
import contract_compat as cc
import drift as D
import latency_p99 as lp
import receipt as R
import rollback_drill as rd

TRAIN = pd.read_parquet(ROOT / "data/silver/train.parquet") if (ROOT / "data/silver/train.parquet").exists() else None
REF = D.load_reference(ROOT / "data/silver/monitoring_reference.json") if (ROOT / "data/silver/monitoring_reference.json").exists() else None
needs_data = __import__("pytest").mark.skipif(TRAIN is None or REF is None, reason="requiere data/silver (reconstruir con la fase 03 y register_model.py)")


# --- comprobante ------------------------------------------------------------------------------

def good_receipt():
    return {"registered_version": "2", "run_id": "r1", "identities": {i: "h" for i in R.IDENTITIES} | {"model": "m"},
            "gates": {g: "pass" for g in R.EVAL_GATES + R.DEPLOY_GATES}}


def test_receipt_accepts_complete_and_rejects_tampered():
    tags = {"run_id": "r1"}
    assert R.validate(good_receipt(), tags, "m", "2") == []
    assert R.validate({}, tags, "m", "2")
    assert R.validate(good_receipt(), tags, "otro-hash", "2")                                   # artefacto distinto
    assert R.validate(good_receipt(), tags, "m", "3")                                            # otra versión
    assert R.validate({**good_receipt(), "gates": {**good_receipt()["gates"], "slice-eval": "fail"}}, tags, "m", "2")
    g = good_receipt(); del g["gates"]["latency-p99"]
    assert R.validate(g, tags, "m", "2")                                                         # gate ausente
    assert cc.check_receipt_mechanism()["ok"]


# --- latencia ---------------------------------------------------------------------------------

def test_latency_gate_fails_over_budget():
    contract = {"assert": [{"metric": "p99_ms", "op": "<=", "value": 250}]}
    assert lp.evaluate([40.0] * 200, contract)[0]["ok"]
    assert not lp.evaluate([40.0] * 190 + [400.0] * 10, contract)[0]["ok"]


# --- rollback ---------------------------------------------------------------------------------

class FakeClient:
    def __init__(self): self.alias = None; self.deleted = False
    def set_registered_model_alias(self, name, alias, version): self.alias = int(version)
    def delete_registered_model_alias(self, name, alias): self.deleted = True


def test_rollback_drill_detects_a_flip_that_does_not_take_effect(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(rd, "MlflowClient", lambda: client)
    monkeypatch.setattr(rd.P, "resolve", lambda name, v, alias: {"version": str(client.alias)})
    monkeypatch.setattr(rd.P, "sample_rows", lambda *a, **k: None)
    monkeypatch.setattr(rd.P, "run_inference", lambda rows, info, **k: pd.DataFrame({"model_version": [int(info["version"])] * 2, "status": ["ok"] * 2}))
    served, failed = rd.drill([1, 2, 1])
    assert served == [1, 2, 1] and not failed and client.deleted
    monkeypatch.setattr(rd.P, "resolve", lambda name, v, alias: {"version": "1"})              # alias «pegado» en v1
    assert rd.drill([1, 2, 1])[0] != [1, 2, 1]
    monkeypatch.setattr(rd.P, "run_inference", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("modelo no carga")))
    assert rd.drill([1, 2])[1] == [1, 2]                                                        # fallos registrados


# --- drift y alertas --------------------------------------------------------------------------

def test_psi_zero_for_identical_and_positive_for_shift():
    a = [0.25, 0.25, 0.25, 0.25]
    assert D.psi(a, a) == 0
    assert D.psi(a, [0.7, 0.1, 0.1, 0.1]) > D.ALERT_PSI


@needs_data
def test_alert_rule_fires_on_injected_drift_and_stays_quiet_without():
    quiet = D.backtest(REF, TRAIN, 40, 200, 1)
    loud = D.backtest(REF, TRAIN, 40, 200, 1, {"column": "sales_channel", "value": "Mobile", "oversample_factor": 5})
    assert quiet["alert_rate"] <= 0.05 and loud["alert_rate"] >= 0.90


@needs_data
def test_false_positive_budget_fails_when_rule_is_too_sensitive():
    too_sensitive = D.backtest(REF, TRAIN, 40, 200, 1, None, alert_psi=0.0)
    assert too_sensitive["alert_rate"] > 0.05                                                  # el gate bloquearía esta regla


def test_signals_report_insufficient_data_instead_of_green():
    if REF is None:
        return
    inf = ab.synthetic_inferences(30) if TRAIN is not None else None
    if inf is None:
        return
    assert {s["status"] for s in D.signals(inf, REF) if s["name"] in ("psi_features", "psi_score", "unseen_categories")} == {"datos insuficientes"}


def test_dashboard_checks_fail_on_external_urls_and_missing_panels(tmp_path):
    good = tmp_path / "ok.html"
    good.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg><script>card("volume", 1)</script>')
    bad = tmp_path / "bad.html"
    bad.write_text('<script src="https://cdn.example.com/x.js"></script>')
    off, panels = {"check": "dashboard_offline"}, {"check": "dashboard_panels", "value": ["volume", "latency"]}
    assert ab.run_check(off, {"dashboard": str(good)}, {})[0]["ok"]
    assert not ab.run_check(off, {"dashboard": str(bad)}, {})[0]["ok"]
    assert not ab.run_check(panels, {"dashboard": str(good)}, {})[0]["ok"]                     # falta «latency»
    assert not ab.run_check(off, {"dashboard": str(tmp_path / "no-existe.html")}, {})[0]["ok"]
