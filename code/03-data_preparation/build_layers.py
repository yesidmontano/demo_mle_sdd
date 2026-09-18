"""Fase 03 — bronze -> silver -> gold. Bronze nunca se escribe.

Ejecutar desde la raíz del repo: python code/03-data_preparation/build_layers.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import avianca_brand as ab
from avianca_brand.colors import GRIS_CLARO, ROJO, TINTA

BRONZE = Path("data/bronze/customer_booking.csv")
SILVER = Path("data/silver/sessions.parquet")
GOLD = Path("data/gold/sessions.parquet")
OUT = Path("results/03-data_preparation")
IMGS = OUT / "imgs"

BUCKET_EDGES = [-1, 7, 30, 90, 180, float("inf")]
BUCKET_LABELS = ["0-7", "8-30", "31-90", "91-180", ">180"]
WANTS = ["wants_extra_baggage", "wants_preferred_seat", "wants_in_flight_meals"]


def to_silver(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.drop_duplicates().reset_index(drop=True)
    for c in ["sales_channel", "trip_type", "flight_day", "route", "booking_origin"]:
        df[c] = df[c].astype("string").str.strip()
    ints = ["num_passengers", "purchase_lead", "length_of_stay", "flight_hour", *WANTS, "booking_complete"]
    df[ints] = df[ints].astype("int64")
    df["flight_duration"] = df["flight_duration"].astype("float64")
    return df


def to_gold(silver: pd.DataFrame) -> pd.DataFrame:
    """Solo transformaciones por fila: nada se aprende del dataset completo."""
    g = silver.copy()
    g["purchase_lead_bucket"] = pd.cut(g["purchase_lead"], BUCKET_EDGES, labels=BUCKET_LABELS).astype("string")
    g["is_weekend_flight"] = g["flight_day"].isin(["Sat", "Sun"]).astype("int64")
    g["extras_count"] = g[WANTS].sum(axis=1).astype("int64")
    return g


def figure(raw: pd.DataFrame, silver: pd.DataFrame, gold: pd.DataFrame) -> str:
    ab.apply_avianca_style()
    fig, axes = ab.create_dashboard(1, 3, title="Limpieza de bronze a silver y feature de gold",
                                    subtitle="Se eliminan duplicados exactos; la forma de la distribución no cambia",
                                    figsize=(14, 5.6))
    n = [len(raw), len(silver)]
    axes[0].bar(["bronze", "silver"], n, color=[GRIS_CLARO.hex, TINTA.hex])
    axes[0].set_title(f"Filas: −{n[0] - n[1]} duplicadas", loc="left", fontsize=11)
    axes[1].hist(raw["purchase_lead"], bins=30, color=GRIS_CLARO.hex, label="bronze")
    axes[1].hist(silver["purchase_lead"], bins=30, color=TINTA.hex, alpha=0.7, label="silver")
    axes[1].legend(), axes[1].set_title("purchase_lead: la forma no cambia", loc="left", fontsize=11)
    c = gold["purchase_lead_bucket"].value_counts().reindex(BUCKET_LABELS)
    axes[2].bar(c.index, c.values, color=ROJO.hex)
    axes[2].set_title("purchase_lead_bucket (gold)", loc="left", fontsize=11)
    IMGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMGS / "antes_despues_limpieza.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return "imgs/antes_despues_limpieza.png"


def main() -> None:
    raw = pd.read_csv(BRONZE, encoding="latin1")
    silver = to_silver(raw)
    gold = to_gold(silver)
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    GOLD.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(SILVER, index=False)
    gold.to_parquet(GOLD, index=False)
    fig = figure(raw, silver, gold)
    dropped = len(raw) - len(silver)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "preparacion.md").write_text(f"""# Preparación de datos

| Capa | Filas | Columnas | Tasa de positivos |
|---|---|---|---|
| bronze | {len(raw):,} | {raw.shape[1]} | {raw.booking_complete.mean():.2%} |
| silver | {len(silver):,} | {silver.shape[1]} | {silver.booking_complete.mean():.2%} |
| gold | {len(gold):,} | {gold.shape[1]} | {gold.booking_complete.mean():.2%} |

![Antes y después]({fig})

Se eliminaron **{dropped}** filas duplicadas exactas (sin id de sesión no se distinguen de un registro doble). La
figura muestra que la forma de `purchase_lead` no cambia y que el efecto es de {dropped / len(raw):.2%} de las filas.

Gold añade `purchase_lead_bucket`, `is_weekend_flight` y `extras_count`, todas por fila. Los encodings de
`route` y `booking_origin` se aprenden en modelado, solo sobre entrenamiento.
""")
    print(f"silver={len(silver)} gold={len(gold)} dropped={dropped}")


if __name__ == "__main__":
    main()
