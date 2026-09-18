"""Fase 04 — entrena línea base y candidato, los registra en MLflow y sella el candidato.

Orden: entrenar -> validar (fuera de pliegue, solo train) -> registrar -> SELLAR. Test no se toca aquí.
Ejecutar desde la raíz del repo: python code/04-modeling/train.py --change <id>
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path("code/05-evaluation").resolve()))
sys.path.insert(0, str(Path("gates").resolve()))
import _contracts as C
import common
import metrics as M
import plots
import preprocessing as pp

MODEL = "conversion-sesion"
OUT = Path("results/04-modeling")
IMGS = OUT / "imgs"

# MLflow serializa sklearn con skops y rechaza tipos que no conoce. Se declaran los del pipeline propio; el
# archivo lo produce este script, no una fuente externa.
TRUSTED_TYPES = ["preprocessing._log1p", "preprocessing.add_row_features",
                 "sklearn.model_selection._split.StratifiedKFold", "sklearn.calibration._CalibratedClassifier",
                 "sklearn.calibration._SigmoidCalibration",
                 "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]
BASELINE_PARAMS = {"C": 1.0, "max_iter": 1000}
CANDIDATE_PARAMS = {"max_iter": 300, "learning_rate": 0.05, "max_leaf_nodes": 31, "early_stopping": True,
                    "calibration": "sigmoid", "calibration_cv": 3}


def make_baseline():
    return LogisticRegression(**BASELINE_PARAMS, random_state=pp.SEED)


def make_candidate():
    hgb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                         early_stopping=True, random_state=pp.SEED)
    return CalibratedClassifierCV(hgb, method="sigmoid", cv=StratifiedKFold(3, shuffle=True, random_state=pp.SEED))


def k_fraction(change: str) -> float:
    """K sale de la spec de evaluation, no del código."""
    return float(next(c["decision"]["k_fraction"] for c in C.load(change, "slice-eval") if "decision" in c))


def train_and_log(name: str, clf, params: dict, pre, x_tr, y_tr, raw_tr, slices, k: float, change: str):
    """Valida fuera de pliegue, ajusta con todo train y registra el pipeline completo."""
    cv = StratifiedKFold(5, shuffle=True, random_state=pp.SEED)
    oof = cross_val_predict(clf, x_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
    val = M.global_metrics(y_tr, oof, k)
    val_slices = M.slice_metrics(y_tr, oof, slices, k)

    t0 = time.time()
    clf.fit(x_tr, y_tr)
    seconds = time.time() - t0
    model = Pipeline([("prep", pre), ("clf", clf)])
    example = raw_tr[pp.INPUT_COLUMNS].head(5)
    signature = infer_signature(raw_tr[pp.INPUT_COLUMNS].head(200), model.predict_proba(raw_tr[pp.INPUT_COLUMNS].head(200)))

    with mlflow.start_run(run_name=f"{MODEL}/{change}/{name}") as run:
        mlflow.set_tags({"change_id": change, "role": name, "phase": "modeling"})
        mlflow.log_params({**params, "seed": pp.SEED, "k_fraction": k, "model_family": type(clf).__name__})
        mlflow.log_metrics({f"val_{k_}": v for k_, v in val.items()} | M.flat(val_slices, "val_")
                           | {"train_seconds": seconds})
        mlflow.sklearn.log_model(sk_model=model, name="model", signature=signature, input_example=example,
                                 pyfunc_predict_fn="predict_proba", skops_trusted_types=TRUSTED_TYPES,
                                 code_paths=["code/03-data_preparation/preprocessing.py"])
        return run.info.run_id, oof, val, val_slices


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True)
    change = ap.parse_args().change
    k = k_fraction(change)

    common.init_mlflow()
    mlflow.set_experiment(common.EXPERIMENT)
    pre = joblib.load(common.STORE / "preprocessing_pipeline.joblib")
    feats = pd.read_parquet(common.STORE / "train_features.parquet")
    x_tr, y_tr = feats.drop(columns=[pp.TARGET]), feats[pp.TARGET].to_numpy()
    raw_tr = common.load_train()
    slices = common.slice_frame(raw_tr)

    b_id, b_oof, b_val, b_sl = train_and_log("baseline", make_baseline(), BASELINE_PARAMS, pre, x_tr, y_tr, raw_tr, slices, k, change)
    c_id, c_oof, c_val, c_sl = train_and_log("candidate", make_candidate(), CANDIDATE_PARAMS, pre, x_tr, y_tr, raw_tr, slices, k, change)

    # Sellado: inmediatamente después de entrenar, antes de mirar ninguna métrica de test.
    r = subprocess.run([sys.executable, "gates/seal.py", "--change", change, "--run-id", c_id,
                        "--baseline-run-id", b_id], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit("No se pudo sellar el candidato: " + r.stdout)

    f1 = plots.slice_figure(b_sl, c_sl, b_val["pr_auc"], c_val["pr_auc"], IMGS / "validacion_por_segmento.png",
                            "Validación: línea base vs candidato", "PR-AUC fuera de pliegue sobre train, global y por segmento")
    f2 = plots.calibration_figure(y_tr, b_oof, c_oof, IMGS / "calibracion_validacion.png",
                                  "Calibración en validación", "Predicciones fuera de pliegue sobre train")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(f"| {m} | {b_val[m]:.4f} | {c_val[m]:.4f} |" for m in b_val)
    (OUT / "modelado.md").write_text(f"""# Modelado

| | Línea base | Candidato |
|---|---|---|
| Modelo | Regresión logística | `HistGradientBoostingClassifier` + calibración sigmoide |
| Run de MLflow | `{b_id}` | `{c_id}` |

Ambos se registran como **pipeline completo** (preprocesamiento + clasificador) con `signature`, `input_example` y
flavor `sklearn`: la entrada es la sesión cruda. Hiperparámetros fijos, sin búsqueda; semilla {pp.SEED}.

## Validación (5 pliegues sobre train; test no se ha tocado)

| Métrica | Línea base | Candidato |
|---|---|---|
{rows}

![Validación por segmento](imgs/{Path(f1).name})

El candidato se compara con la línea base global y por segmento; los segmentos que empeoran salen en rojo.

![Calibración en validación](imgs/{Path(f2).name})

**Límite**: las features de train ya llevan el target encoding con validación cruzada del pipeline, así que la
validación es ligeramente optimista; la cifra decisoria es la de test (fase 05).

## Sellado

El candidato quedó sellado en `openspec/changes/{change}/evidence/seal.json` **antes** de evaluar en test.
""")
    print(json.dumps({"baseline": b_id, "candidate": c_id, "val_pr_auc": [b_val["pr_auc"], c_val["pr_auc"]]}))


if __name__ == "__main__":
    main()
