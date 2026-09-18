"""Pipeline de preprocesamiento de `conversion-sesion`. Sin E/S: solo lo define.

Es el contrato entre entrenamiento y serving: `run_preparation.py` lo ajusta con
train y lo guarda; serving importa este módulo (o carga el joblib) y lo aplica
tal cual. Entrada: filas con las columnas de `INPUT_COLUMNS`. Salida: DataFrame.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler, TargetEncoder

TARGET = "booking_complete"
WANTS = ["wants_extra_baggage", "wants_preferred_seat", "wants_in_flight_meals"]
NUMERIC = ["num_passengers", "flight_hour", "flight_duration"]
LOG_NUMERIC = ["purchase_lead", "length_of_stay"]
CATEGORICAL = ["sales_channel", "trip_type", "flight_day"]
HIGH_CARD = ["route", "booking_origin"]
INPUT_COLUMNS = [*NUMERIC, *LOG_NUMERIC, *CATEGORICAL, *HIGH_CARD, *WANTS]

BUCKET_EDGES = [-1, 7, 30, 90, 180, float("inf")]
BUCKET_LABELS = ["0-7", "8-30", "31-90", "91-180", ">180"]
SEED = 42


def add_row_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derivadas por fila: no aprenden nada, solo leen la misma fila."""
    out = df.copy()
    out["purchase_lead_bucket"] = pd.cut(out["purchase_lead"], BUCKET_EDGES, labels=BUCKET_LABELS).astype(str)
    out["is_weekend_flight"] = out["flight_day"].isin(["Sat", "Sun"]).astype(int)
    out["extras_count"] = out[WANTS].sum(axis=1).astype(int)
    return out


def _log1p(x):
    return np.log1p(x)


def build_pipeline() -> Pipeline:
    """Pipeline sin ajustar. Se ajusta SOLO con train."""
    ct = ColumnTransformer(
        [
            ("num", StandardScaler(), [*NUMERIC, "extras_count"]),
            ("log", Pipeline([("log1p", FunctionTransformer(_log1p, feature_names_out="one-to-one")),
                              ("scale", StandardScaler())]), LOG_NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             [*CATEGORICAL, "purchase_lead_bucket"]),
            ("high", TargetEncoder(target_type="binary", cv=StratifiedKFold(5, shuffle=True, random_state=SEED)), HIGH_CARD),
            ("bin", "passthrough", [*WANTS, "is_weekend_flight"]),
        ],
        verbose_feature_names_out=False,
    )
    return Pipeline([("row_features", FunctionTransformer(add_row_features)), ("encode", ct)]).set_output(transform="pandas")
