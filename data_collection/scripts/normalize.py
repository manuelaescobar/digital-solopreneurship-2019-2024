#!/usr/bin/env python3
"""
Normaliza el crudo de data/raw/<fuente>/*.json a la tabla unificada
definida en schema/esquema_unificado.md, y la guarda en
data/processed/entities.csv (+ un resumen por fuente).

Concatena TODOS los archivos de cada fuente en data/raw/<fuente>/*.json
(cada corrida de ingesta escribe un archivo nuevo con timestamp - para
fuentes multi-anio como stackoverflow_survey cada archivo es un anio
distinto, no una version mas completa de la anterior). La deduplicacion
por entity_id al final resuelve con seguridad los casos donde una corrida
si superpone a otra (ej. una corrida de github mas chica de prueba,
contenida en una corrida posterior mas grande).

Uso:
    python3 normalize.py
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

UNIFIED_COLUMNS = [
    "entity_id", "source", "source_native_id", "entity_type",
    "name_or_title", "description_text", "url", "created_at", "retrieved_at",
    "author_handle", "maker_count", "metric_primary", "metric_secondary",
    "revenue_signal", "category_raw", "structural_signal", "intentional_signal",
    "leverage_signal", "is_solopreneur_candidate", "labeling_method",
    "raw_source_path",
]


def to_unified_row(record, raw_path):
    row = {col: record.get(col) for col in UNIFIED_COLUMNS}
    row["raw_source_path"] = str(raw_path.relative_to(ROOT))
    # category_raw puede venir como lista -> se serializa a string legible
    if isinstance(row.get("category_raw"), list):
        row["category_raw"] = "; ".join(str(c) for c in row["category_raw"])
    return row


def load_source(source_dir):
    rows = []
    for f in sorted(source_dir.glob("*.json")):
        try:
            records = json.loads(f.read_text())
        except json.JSONDecodeError:
            print(f"  aviso: {f} no es JSON valido, se omite")
            continue
        for rec in records:
            rows.append(to_unified_row(rec, f))
    return rows


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    if not RAW_DIR.exists():
        raise SystemExit("ERROR: no existe data/raw/ - corre alguna ingesta primero")

    all_rows = []
    for source_dir in sorted(RAW_DIR.iterdir()):
        if not source_dir.is_dir():
            continue
        print(f"Procesando fuente: {source_dir.name}")
        rows = load_source(source_dir)
        print(f"  {len(rows)} registros")
        all_rows.extend(rows)

    if not all_rows:
        raise SystemExit("ERROR: no se encontraron registros en data/raw/")

    df = pd.DataFrame(all_rows, columns=UNIFIED_COLUMNS)

    before = len(df)
    df = df.drop_duplicates(subset="entity_id", keep="last")
    after = len(df)
    if before != after:
        print(f"\nDeduplicados {before - after} registros repetidos por entity_id")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = PROCESSED_DIR / "entities.csv"
    df.to_csv(out_csv, index=False)

    # Resumen por fuente: conteo total y candidatos solopreneur (donde aplica)
    summary = (
        df.groupby("source")
        .agg(
            total_registros=("entity_id", "count"),
            candidatos_solopreneur=("is_solopreneur_candidate", lambda s: (s == True).sum()),
        )
        .reset_index()
    )
    summary_path = PROCESSED_DIR / "summary_by_source.csv"
    summary.to_csv(summary_path, index=False)

    print(f"\n=== Resumen ===")
    print(summary.to_string(index=False))
    print(f"\nTotal filas en tabla unificada: {len(df)}")
    print(f"Guardado en: {out_csv}")
    print(f"Resumen guardado en: {summary_path}")


if __name__ == "__main__":
    main()
