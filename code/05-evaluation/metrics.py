"""Métricas de evaluación de `conversion-sesion`. Las usan train.py, evaluate.py y los gates.

Una sola implementación: si el script y el gate calcularan cada uno lo suyo, podrían discrepar.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

SLICES = ["sales_channel", "trip_type", "purchase_lead_bucket"]
MIN_SLICE_SIZE = 500


def captured_conversions_at_k(y, p, k_fraction: float) -> float:
    """Fracción de todas las conversiones que caen en el top-K del ranking."""
    y, p = np.asarray(y), np.asarray(p)
    n_top = max(1, int(round(len(y) * k_fraction)))
    top = np.argsort(-p, kind="stable")[:n_top]
    return float(y[top].sum() / max(1, y.sum()))


def ece(y, p, bins: int = 10) -> float:
    """Error de calibración esperado, con intervalos de igual ancho."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    idx = np.minimum((p * bins).astype(int), bins - 1)
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(total)


def global_metrics(y, p, k_fraction: float) -> dict:
    return {"pr_auc": float(average_precision_score(y, p)),
            "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "roc_auc": float(roc_auc_score(y, p)),
            "brier": float(brier_score_loss(y, p)),
            "ece": ece(y, p),
            "captured_conversions_at_k": captured_conversions_at_k(y, p, k_fraction)}


def slice_metrics(y, p, slices: pd.DataFrame, k_fraction: float, min_size: int = MIN_SLICE_SIZE) -> dict:
    """{columna: {valor: {n, pr_auc, captured_conversions_at_k}}} solo para segmentos con `min_size` o más."""
    y, p, out = np.asarray(y), np.asarray(p), {}
    for col in slices.columns:
        out[col] = {}
        for val in sorted(slices[col].astype(str).unique()):
            m = (slices[col].astype(str) == val).to_numpy()
            if m.sum() >= min_size and y[m].min() != y[m].max():
                out[col][val] = {"n": int(m.sum()),
                                 "pr_auc": float(average_precision_score(y[m], p[m])),
                                 "captured_conversions_at_k": captured_conversions_at_k(y[m], p[m], k_fraction)}
    return out


def flat(metrics: dict, prefix: str = "") -> dict:
    """Aplana métricas por segmento para `mlflow.log_metrics` (claves sin espacios ni símbolos)."""
    out = {}
    for col, vals in metrics.items():
        for val, m in vals.items():
            safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in str(val))
            for name, v in m.items():
                if name != "n":
                    out[f"{prefix}slice_{col}_{safe}_{name}"] = v
    return out
