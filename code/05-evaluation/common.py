"""Carga de datos, sello y modelos MLflow, compartida por evaluate.py y los gates."""
import json
import sys
from pathlib import Path

import mlflow
import pandas as pd

sys.path.insert(0, str(Path("code/03-data_preparation").resolve()))
import preprocessing as pp

TRACKING_URI = "sqlite:///mlflow.db"
ARTIFACTS = Path("mlartifacts")
EXPERIMENT = "conversion-sesion"
STORE = Path("data/silver")


def init_mlflow() -> None:
    """Seguimiento local en SQLite; los artefactos van a `mlartifacts/` (ninguno se versiona)."""
    mlflow.set_tracking_uri(TRACKING_URI)
    if mlflow.get_experiment_by_name(EXPERIMENT) is None:
        mlflow.create_experiment(EXPERIMENT, artifact_location=ARTIFACTS.resolve().as_uri())


def seal_path(change: str) -> Path:
    return Path("openspec/changes", change, "evidence", "seal.json")


def load_seal(change: str) -> dict:
    return json.loads(seal_path(change).read_text())


def load_model(run_id: str):
    init_mlflow()
    return mlflow.sklearn.load_model(f"runs:/{run_id}/model")


def load_test() -> pd.DataFrame:
    return pd.read_parquet(STORE / "test.parquet")


def load_train() -> pd.DataFrame:
    return pd.read_parquet(STORE / "train.parquet")


def slice_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Columnas de segmento a partir de sesiones crudas (el bucket es derivado por fila)."""
    return pp.add_row_features(raw)[["sales_channel", "trip_type", "purchase_lead_bucket"]]


def proba(model, raw: pd.DataFrame):
    """Probabilidad de conversión (clase 1) a partir de sesiones crudas."""
    return model.predict_proba(raw[pp.INPUT_COLUMNS])[:, 1]


def score(change: str, k_fraction: float) -> dict:
    """Puntúa línea base y candidato sellados sobre test: probabilidades y métricas globales y por segmento."""
    import metrics as M

    seal = load_seal(change)
    raw = load_test()
    y = raw[pp.TARGET].to_numpy()
    slices = slice_frame(raw)
    out = {"seal": seal, "raw": raw, "y": y, "slices": slices, "k": k_fraction}
    for role, run_id in (("baseline", seal["baseline_run_id"]), ("candidate", seal["run_id"])):
        p = proba(load_model(run_id), raw)
        out[role] = {"p": p, "global": M.global_metrics(y, p, k_fraction),
                     "slices": M.slice_metrics(y, p, slices, k_fraction)}
    return out


REGISTERED_MODEL = "conversion-sesion"
