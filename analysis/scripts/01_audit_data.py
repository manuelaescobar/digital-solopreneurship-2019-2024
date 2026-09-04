#!/usr/bin/env python3
"""
Fase 1.1 - Auditoria de datos.

El archivo entities.csv es una UNION estructural de 6 fuentes con
entity_type distintos (person, aggregate_country_year, aggregate_geo_sector,
repository, paper). No es una tabla analizable fila a fila tal cual: cada
entity_type tiene una unidad de analisis distinta y variables que solo
tienen sentido dentro de su propia fuente. Este script separa en
sub-tablas y audita cada una por separado (tipos, missingness, N, rango
de fechas) antes de cualquier limpieza o modelado.

Salida: analysis/outputs/tables/audit_<source>.csv (missingness por columna)
        + resumen impreso en consola.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ENTITIES_PATH = ROOT / "data_collection" / "data" / "processed" / "entities.csv"
OUT_TABLES = Path(__file__).resolve().parent.parent / "outputs" / "tables"
OUT_TABLES.mkdir(parents=True, exist_ok=True)

# Columnas relevantes por sub-tabla (mas alla de las genericas del esquema
# unificado) segun lo que cada fuente realmente puebla.
RELEVANT_COLS = {
    "stackoverflow_survey": [
        "structural_signal", "is_solopreneur_candidate", "metric_primary",
        "created_at",
    ],
    "worldbank": ["metric_primary"] ,  # placeholder; el valor real esta fuera del esquema unificado
    "eurostat": [],
    "census_nes": [],
    "github": ["metric_primary", "metric_secondary", "structural_signal"],
    "openalex": ["metric_primary"],
}


def audit_source(df, source):
    sub = df[df["source"] == source].copy()
    n = len(sub)
    dates = pd.to_datetime(sub["created_at"], errors="coerce", utc=True, format="mixed")
    date_min = dates.min()
    date_max = dates.max()

    missing = sub.isna().mean().sort_values(ascending=False)
    missing = missing[missing > 0]  # solo columnas con al menos 1 faltante

    print(f"\n=== {source} (N={n}, entity_type={sub['entity_type'].unique().tolist()}) ===")
    print(f"  rango created_at: {date_min} .. {date_max}")
    print(f"  duplicados en entity_id: {sub['entity_id'].duplicated().sum()}")
    if len(missing) > 0:
        print("  columnas con datos faltantes (%):")
        for col, pct in missing.items():
            print(f"    {col}: {pct*100:.1f}%")
    else:
        print("  sin columnas con faltantes en el esquema unificado")

    out = sub.isna().mean().rename("pct_missing").reset_index().rename(columns={"index": "column"})
    out["n"] = n
    out.to_csv(OUT_TABLES / f"audit_{source}.csv", index=False)
    return sub


def main():
    df = pd.read_csv(ENTITIES_PATH, low_memory=False)
    print(f"Tabla unificada: {df.shape[0]} filas, {df.shape[1]} columnas")
    print(f"Fuentes: {sorted(df['source'].unique())}")

    for source in sorted(df["source"].unique()):
        audit_source(df, source)

    print("\n" + "=" * 60)
    print("NOTA METODOLOGICA: las 6 fuentes tienen unidades de analisis")
    print("incompatibles (persona / pais-anio / geo-sector / repositorio /")
    print("paper). No se debe modelar la tabla unificada como un solo pool -")
    print("cada sub-tabla requiere su propia limpieza y su propio analisis.")
    print("=" * 60)


if __name__ == "__main__":
    main()
