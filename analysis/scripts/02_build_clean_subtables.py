#!/usr/bin/env python3
"""
Fase 1.2 - Limpieza reproducible, por sub-tabla.

entities.csv (el esquema unificado generico) pierde la columna de VALOR
real para las fuentes agregadas (worldbank/eurostat/census_nes), porque
ese esquema fue disenado pensando en entidades tipo "post"/"paper"/"repo",
no en observaciones pais-anio. Este script lee directo el crudo de
data_collection/data/raw/<fuente>/*.json y construye una tabla limpia por
fuente, con sus columnas propias, tipos correctos, y decisiones de
limpieza documentadas inline.

Salida: analysis/data/<fuente>_clean.csv
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data_collection" / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_all_json(source_dir, dedup_by_entity_id=False):
    rows = []
    for f in sorted(source_dir.glob("*.json")):
        rows.extend(json.loads(f.read_text()))
    if dedup_by_entity_id:
        # varias corridas del mismo scraper se superponen (ej. una corrida
        # de prueba mas chica contenida en una posterior mas grande) -
        # se queda con la ultima ocurrencia de cada entity_id.
        by_id = {r["entity_id"]: r for r in rows}
        before = len(rows)
        rows = list(by_id.values())
        if before != len(rows):
            print(f"  ({source_dir.name}) deduplicadas {before - len(rows)} filas por entity_id")
    return rows


def clean_worldbank():
    rows = load_all_json(RAW_DIR / "worldbank")
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    # is_aggregate=True son agrupaciones regionales/de ingreso del propio
    # World Bank (ej. "High income"), no paises - se conservan pero
    # marcadas, para poder excluirlas de un analisis por pais.
    df["is_aggregate"] = df["is_aggregate"].fillna(False)
    before = len(df)
    df = df.dropna(subset=["value"])  # sin valor, la fila no aporta nada
    print(f"worldbank: {before} -> {len(df)} filas tras quitar value=NaN "
          f"({before - len(df)} filas, {(before-len(df))/before*100:.1f}%)")
    cols = ["entity_id", "country_iso3", "country_name", "is_aggregate",
            "year", "indicator_code", "indicator_field", "value"]
    df[cols].to_csv(OUT_DIR / "worldbank_clean.csv", index=False)
    return df[cols]


def clean_eurostat():
    rows = load_all_json(RAW_DIR / "eurostat")
    df = pd.DataFrame(rows)
    df["value_thousands"] = pd.to_numeric(df["value_thousands"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    before = len(df)
    df = df.dropna(subset=["value_thousands"])
    print(f"eurostat: {before} -> {len(df)} filas tras quitar value=NaN "
          f"({before - len(df)} filas)")
    cols = ["entity_id", "country_code", "country_name", "year",
            "work_status", "work_status_label", "sex", "age_group",
            "occupation", "unit", "value_thousands"]
    df[cols].to_csv(OUT_DIR / "eurostat_clean.csv", index=False)
    return df[cols]


def clean_census_nes():
    rows = load_all_json(RAW_DIR / "census_nes")
    df = pd.DataFrame(rows)
    df["nonemployer_establishments"] = pd.to_numeric(df["nonemployer_establishments"], errors="coerce")
    df["nonemployer_receipts_thousands"] = pd.to_numeric(df["nonemployer_receipts_thousands"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    cols = ["entity_id", "geography", "naics2017", "year",
            "nonemployer_establishments", "nonemployer_receipts_thousands"]
    df[cols].to_csv(OUT_DIR / "census_nes_clean.csv", index=False)
    return df[cols]


def clean_github():
    rows = load_all_json(RAW_DIR / "github", dedup_by_entity_id=True)
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["stars"] = pd.to_numeric(df["metric_primary"], errors="coerce")
    df["forks"] = pd.to_numeric(df["metric_secondary"], errors="coerce")
    cols = ["entity_id", "name_or_title", "description_text", "url",
            "created_at", "author_handle", "owner_type", "structural_signal",
            "stars", "forks", "language", "topics", "matched_query"]
    df[cols].to_csv(OUT_DIR / "github_clean.csv", index=False)
    return df[cols]


def clean_openalex():
    rows = load_all_json(RAW_DIR / "openalex")
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["citations"] = pd.to_numeric(df["metric_primary"], errors="coerce")
    cols = ["entity_id", "name_or_title", "description_text", "url",
            "created_at", "authors", "citations", "category_raw", "venue",
            "matched_query"]
    df[cols].to_csv(OUT_DIR / "openalex_clean.csv", index=False)
    return df[cols]


def clean_so_survey():
    rows = load_all_json(RAW_DIR / "stackoverflow_survey")
    df = pd.DataFrame(rows)
    # ConvertedCompYearly/Salary vienen como texto, incluyendo literal "NA"
    df["income_usd"] = pd.to_numeric(df["metric_primary"], errors="coerce")
    df["years_experience_pro"] = pd.to_numeric(df["years_experience_pro"], errors="coerce")
    n_income_missing = df["income_usd"].isna().sum()
    print(f"so_survey: income_usd faltante en {n_income_missing}/{len(df)} "
          f"({n_income_missing/len(df)*100:.1f}%) - no se elimina aqui, "
          f"se diagnostica el mecanismo de perdida en el paso siguiente")
    cols = ["entity_id", "survey_year", "country", "years_experience_pro",
            "org_size_raw", "dev_type_raw", "income_usd",
            "structural_signal", "is_solopreneur_candidate",
            "org_size_granularity"]
    df[cols].to_csv(OUT_DIR / "so_survey_clean.csv", index=False)
    return df[cols]


def main():
    builders = {
        "worldbank": clean_worldbank,
        "eurostat": clean_eurostat,
        "census_nes": clean_census_nes,
        "github": clean_github,
        "openalex": clean_openalex,
        "stackoverflow_survey": clean_so_survey,
    }
    for name, fn in builders.items():
        print(f"\n--- {name} ---")
        df = fn()
        print(f"  guardado: {len(df)} filas, {len(df.columns)} columnas -> "
              f"analysis/data/{name if name != 'stackoverflow_survey' else 'so_survey'}_clean.csv")


if __name__ == "__main__":
    main()
