"""Fase 03 — limpieza -> split -> feature engineering, guardado en el feature store.

Orden deliberado: el split va ANTES del feature engineering; el pipeline se ajusta
solo con train. Feature store = data/silver/. Bronze nunca se escribe; gold no se toca.
Ejecutar desde la raíz del repo: python code/03-data_preparation/run_preparation.py
"""
import hashlib
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent))
import preprocessing as pp

import avianca_brand as ab
from avianca_brand.colors import GRIS_CLARO, ROJO, TINTA

BRONZE = Path("data/bronze/customer_booking.csv")
STORE = Path("data/silver")
OUT = Path("results/03-data_preparation")
IMGS = OUT / "imgs"
TEST_SIZE = 0.20


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Limpieza y formateo: duplicados exactos, texto recortado, tipos explícitos."""
    df = raw.drop_duplicates().reset_index(drop=True)
    for c in ["sales_channel", "trip_type", "flight_day", "route", "booking_origin"]:
        df[c] = df[c].astype("string").str.strip()
    ints = ["num_passengers", "purchase_lead", "length_of_stay", "flight_hour", *pp.WANTS, pp.TARGET]
    df[ints] = df[ints].astype("int64")
    df["flight_duration"] = df["flight_duration"].astype("float64")
    return df


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_figures(clean_df, train, test, x_train) -> tuple[str, str]:
    ab.apply_avianca_style()
    IMGS.mkdir(parents=True, exist_ok=True)
    fig, axes = ab.create_dashboard(1, 2, title="Split train/test estratificado",
                                    subtitle="Mismo tamaño relativo y misma tasa de positivos en ambos conjuntos",
                                    figsize=(12, 5.4))
    axes[0].bar(["train", "test"], [len(train), len(test)], color=[TINTA.hex, GRIS_CLARO.hex])
    axes[0].set_title("Filas por conjunto")
    rates = [d[pp.TARGET].mean() * 100 for d in (clean_df, train, test)]
    axes[1].bar(["total", "train", "test"], rates, color=[GRIS_CLARO.hex, TINTA.hex, ROJO.hex])
    axes[1].set_ylim(0, max(rates) * 1.3)
    for i, r in enumerate(rates):
        axes[1].text(i, r + 0.3, f"{r:.2f} %", ha="center")
    axes[1].set_title("% de positivos")
    fig.savefig(IMGS / "split_estratificado.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = ab.create_dashboard(1, 2, title="Efecto del pipeline en purchase_lead",
                                    subtitle="log1p y escalado ajustados con train: colas largas a una escala comparable",
                                    figsize=(12, 5.4))
    axes[0].hist(train["purchase_lead"], bins=40, color=GRIS_CLARO.hex)
    axes[0].set_title("Crudo (días)")
    axes[1].hist(x_train["purchase_lead"], bins=40, color=TINTA.hex)
    axes[1].set_title("Transformado (log1p + estandarizado)")
    fig.savefig(IMGS / "pipeline_purchase_lead.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return "imgs/split_estratificado.png", "imgs/pipeline_purchase_lead.png"


def main() -> None:
    raw = pd.read_csv(BRONZE, encoding="latin1")
    sessions = clean(raw)

    train, test = train_test_split(sessions, test_size=TEST_SIZE, stratify=sessions[pp.TARGET],
                                   random_state=pp.SEED)
    train, test = train.reset_index(drop=True), test.reset_index(drop=True)

    pipe = pp.build_pipeline()
    x_train = pipe.fit_transform(train[pp.INPUT_COLUMNS], train[pp.TARGET])   # solo train
    x_test = pipe.transform(test[pp.INPUT_COLUMNS])                            # test no reajusta

    STORE.mkdir(parents=True, exist_ok=True)
    files = {
        "sessions": sessions, "train": train, "test": test,
        "train_features": x_train.assign(**{pp.TARGET: train[pp.TARGET].values}),
        "test_features": x_test.assign(**{pp.TARGET: test[pp.TARGET].values}),
    }
    for name, df in files.items():
        df.to_parquet(STORE / f"{name}.parquet", index=False)
    joblib.dump(pipe, STORE / "preprocessing_pipeline.joblib")

    manifest = {
        "seed": pp.SEED, "test_size": TEST_SIZE, "sklearn_version": sklearn.__version__,
        "rows": {k: len(v) for k, v in files.items()},
        "positive_rate": {k: round(float(v[pp.TARGET].mean()), 6) for k, v in files.items()},
        "input_columns": pp.INPUT_COLUMNS, "output_columns": list(x_train.columns), "target": pp.TARGET,
        "sha256": {p.name: sha256(p) for p in sorted(STORE.glob("*")) if p.suffix in {".parquet", ".joblib"}},
    }
    (STORE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    f_split, f_pipe = save_figures(sessions, train, test, x_train)
    inv = "\n".join(f"| `{p.name}` | {p.stat().st_size / 1024:,.0f} KB |" for p in sorted(STORE.glob("*"))
                    if p.name != ".gitkeep")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "preparacion.md").write_text(f"""# Preparación de datos

## Orden del proceso

1. **Limpieza y formateo** (bronze → `sessions.parquet`): {len(raw) - len(sessions)} duplicados exactos eliminados, texto recortado, tipos explícitos.
2. **Split** train/test 80/20, estratificado por `booking_complete`, semilla {pp.SEED}. Va **antes** del feature engineering.
3. **Feature engineering**: el pipeline se **ajusta solo con train** y se aplica a test. Incluye derivadas por fila, `log1p` y escalado
   de numéricas, one-hot de categóricas y target encoding de `route` y `booking_origin`.

![Split estratificado]({f_split})

Train tiene {len(train):,} filas ({train[pp.TARGET].mean():.2%} positivos) y test {len(test):,} ({test[pp.TARGET].mean():.2%}): la
estratificación conserva la clase minoritaria en ambos.

![Efecto del pipeline]({f_pipe})

## Feature store (`data/silver/`)

| Artefacto | Tamaño |
|---|---|
{inv}

- `train.parquet` / `test.parquet`: limpios, columnas originales. Entrada del pipeline en serving.
- `train_features.parquet` / `test_features.parquet`: transformados, con `booking_complete`. Entrada del modelo en las fases 04 y 05.
- `preprocessing_pipeline.joblib`: pipeline ajustado con train. Se define en [`preprocessing.py`](../../code/03-data_preparation/preprocessing.py).
- `manifest.json`: semilla, versión de sklearn, conteos, columnas de entrada y salida, hashes.

`data/gold/` queda vacía: se reserva a datos de inferencia y pruebas de despliegue.

**Límite declarado**: no hay id de cliente ni de sesión, así que el split es por fila.
""")
    print("train", len(train), "test", len(test), "features", x_train.shape[1])


if __name__ == "__main__":
    main()
