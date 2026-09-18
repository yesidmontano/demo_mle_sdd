"""Fase 05 — evalúa UNA vez, sobre test, el candidato sellado y la línea base.

Ejecutar desde la raíz del repo: python code/05-evaluation/evaluate.py --change <id>
K sale de la spec de evaluation. Los umbrales los aplica `gates/slice_eval.py`; aquí solo se
reutiliza su función `judge` para redactar el informe con el mismo criterio.
"""
import argparse
import sys
from pathlib import Path

import mlflow

sys.path.insert(0, str(Path("gates").resolve()))
sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
import _contracts as C
import common
import metrics as M
import plots
import slice_eval

OUT = Path("results/05-evaluation")
IMGS = OUT / "imgs"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True)
    change = ap.parse_args().change
    contracts = C.load(change, "slice-eval")
    k = float(next(c["decision"]["k_fraction"] for c in contracts if "decision" in c))

    common.init_mlflow()
    mlflow.set_experiment(common.EXPERIMENT)
    s = common.score(change, k)
    base, cand, y = s["baseline"], s["candidate"], s["y"]

    with mlflow.start_run(run_name=f"conversion-sesion/{change}/evaluation"):
        mlflow.set_tags({"change_id": change, "phase": "evaluation", "sealed_run_id": s["seal"]["run_id"]})
        mlflow.log_param("k_fraction", k)
        for role in ("baseline", "candidate"):
            mlflow.log_metrics({f"test_{role}_{n}": v for n, v in s[role]["global"].items()}
                               | M.flat(s[role]["slices"], f"test_{role}_"))

    f_slice = plots.slice_figure(base["slices"], cand["slices"], base["global"]["pr_auc"], cand["global"]["pr_auc"],
                                 IMGS / "test_por_segmento.png", "Test: línea base vs candidato",
                                 "PR-AUC sobre test, global y por segmento (segmentos con 500+ sesiones)")
    f_gain = plots.gains_figure(y, base["p"], cand["p"], k, IMGS / "ganancia_top_k.png",
                                "Conversiones capturadas al intervenir el top del ranking",
                                f"Con K = {k:.0%} se captura la fracción marcada en el eje vertical")
    f_cal = plots.calibration_figure(y, base["p"], cand["p"], IMGS / "calibracion_test.png",
                                     "Calibración en test", "La probabilidad debe significar lo que dice")

    checks = slice_eval.judge(cand, base, contracts)
    failed = [c for c in checks if not c["ok"]]
    verdict = ("**El candidato cumple los umbrales de la spec.**" if not failed else
               f"**El candidato NO cumple {len(failed)} de {len(checks)} umbrales**; no se promueve.")
    worse = [f"{col} = {val} ({sm['pr_auc'] - base['slices'][col][val]['pr_auc']:+.3f} PR-AUC)"
             for col, vals in cand["slices"].items() for val, sm in vals.items()
             if sm["pr_auc"] < base["slices"][col][val]["pr_auc"]]
    within = "\n".join(f"- {w}: retrocede pero dentro de la tolerancia de 0,02." for w in worse) or "- Ninguno."
    g = lambda role, m: s[role]["global"][m]
    rows = "\n".join(f"| {m} | {g('baseline', m):.4f} | {g('candidate', m):.4f} |" for m in base["global"])
    fails = "\n".join(f"- {c['check']}: candidato {c['candidate']} frente a {c['reference']}" for c in failed) or "- Ninguno."
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evaluacion.md").write_text(f"""# Evaluación en test

Modelo evaluado: el sellado en `openspec/changes/{change}/evidence/seal.json` (run `{s['seal']['run_id']}`).
Test se evaluó **una sola vez**, después del sellado. Regla de decisión: intervenir el top **{k:.0%}** del ranking.

## Veredicto

{verdict}

| Métrica (test) | Línea base | Candidato |
|---|---|---|
{rows}

![Test por segmento](imgs/{Path(f_slice).name})

PR-AUC por segmento: los segmentos que empeoran frente a la línea base salen en rojo con el delta impreso.

![Ganancia acumulada](imgs/{Path(f_gain).name})

Con K = {k:.0%}, el candidato captura {g('candidate', 'captured_conversions_at_k'):.1%} de las conversiones y la línea base
{g('baseline', 'captured_conversions_at_k'):.1%}; intervenir al azar capturaría {k:.0%}.

![Calibración en test]({'imgs/' + Path(f_cal).name})

ECE del candidato: {g('candidate', 'ece'):.4f} (umbral 0,05).

## Umbrales incumplidos

{fails}

## Segmentos donde el candidato retrocede

{within}

## Límites

- Split por fila, sin id de cliente: las cifras son una cota optimista.
- Sin fecha no hay validación temporal.
- El ticket medio sigue siendo un supuesto: estas métricas miden ranking, no ingreso.
""")
    print("evaluado:", "cumple" if not failed else f"{len(failed)} umbrales incumplidos", "| checks", len(checks))


if __name__ == "__main__":
    main()
