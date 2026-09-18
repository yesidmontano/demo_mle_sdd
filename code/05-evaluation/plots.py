"""Figuras de modelado y evaluación con el sistema de marca."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import avianca_brand as ab
from avianca_brand.colors import GRIS_CLARO, GRIS_MEDIO, ROJO, TEAL, TINTA


def _save(fig, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def slice_figure(base: dict, cand: dict, glob_base: float, glob_cand: float, path: Path,
                 title: str, subtitle: str, metric: str = "pr_auc") -> str:
    """Línea base vs candidato: global y por segmento (la gráfica que exige el marco)."""
    ab.apply_avianca_style()
    labels, b, c = ["GLOBAL"], [glob_base], [glob_cand]
    for col, vals in cand.items():
        for val, m in vals.items():
            labels.append(f"{col} = {val}  (n={m['n']:,})")
            b.append(base[col][val][metric])
            c.append(m[metric])
    fig, _ = ab.slice_chart(labels, b, c, metric="PR-AUC (mayor es mejor)", title=title, subtitle=subtitle,
                            lower_is_better=False, figsize=(11, 0.42 * len(labels) + 2.6))
    return _save(fig, path)


def calibration_figure(y, p_base, p_cand, path: Path, title: str, subtitle: str, bins: int = 10) -> str:
    ab.apply_avianca_style()
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.plot([0, 1], [0, 1], color=GRIS_MEDIO.hex, ls="--", lw=1.2, label="Calibración perfecta")
    for p, name, color in ((p_base, "Línea base", GRIS_MEDIO.hex), (p_cand, "Candidato", ROJO.hex)):
        idx = np.minimum((np.asarray(p) * bins).astype(int), bins - 1)
        xs = [np.mean(np.asarray(p)[idx == k]) for k in range(bins) if (idx == k).sum() >= 30]
        ys = [np.mean(np.asarray(y)[idx == k]) for k in range(bins) if (idx == k).sum() >= 30]
        ax.plot(xs, ys, marker="o", color=color, label=name)
    ax.set_xlabel("Probabilidad predicha"), ax.set_ylabel("Frecuencia observada de conversión")
    ax.legend(loc="upper left")
    ab.style_axes(ax, title, subtitle)
    return _save(fig, path)


def gains_figure(y, p_base, p_cand, k_fraction: float, path: Path, title: str, subtitle: str) -> str:
    """Conversiones acumuladas capturadas al ir intervenendo del más al menos probable."""
    ab.apply_avianca_style()
    y = np.asarray(y)
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    frac = np.arange(1, len(y) + 1) / len(y)
    ax.plot([0, 1], [0, 1], color=GRIS_CLARO.hex, ls="--", label="Al azar")
    for p, name, color in ((p_base, "Línea base", GRIS_MEDIO.hex), (p_cand, "Candidato", ROJO.hex)):
        order = np.argsort(-np.asarray(p), kind="stable")
        ax.plot(frac, np.cumsum(y[order]) / y.sum(), color=color, label=name)
    ax.axvline(k_fraction, color=TINTA.hex, lw=1)
    ax.text(k_fraction + 0.01, 0.05, f"K = {k_fraction:.0%}", color=TINTA.hex)
    ax.set_xlabel("Fracción de sesiones intervenidas"), ax.set_ylabel("Fracción de conversiones capturadas")
    ax.legend(loc="lower right")
    ab.style_axes(ax, title, subtitle)
    return _save(fig, path)
