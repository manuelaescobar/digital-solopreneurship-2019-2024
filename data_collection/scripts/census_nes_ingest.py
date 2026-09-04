#!/usr/bin/env python3
"""
Ingesta de US Census Bureau - Nonemployer Statistics (NES): negocios con
ingresos pero 0 empleados, por sector (NAICS) y geografia.

Requiere una API key gratuita (registro instantaneo por email, sin
captcha ni verificacion de cuenta): https://api.census.gov/data/key_signup.html
Ponla en .env como CENSUS_API_KEY.

Por defecto trae, para EEUU y cada estado, el numero de establecimientos
(NESTAB) y los ingresos totales (NRCPTOT) para los sectores NAICS mas
relevantes a solopreneurship digital:
  51 - Information
  54 - Professional, Scientific, and Technical Services
  71 - Arts, Entertainment, and Recreation
  81 - Other Services

Uso:
    python3 census_nes_ingest.py --year 2021
    python3 census_nes_ingest.py --year 2021 --naics 51,54,71,81 --geo state
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("CENSUS_API_KEY")
DEFAULT_NAICS = ["51", "54", "71", "81"]


def fetch_naics(session, year, naics_code, geo):
    for_clause = "us:*" if geo == "us" else "state:*"
    params = {
        "get": "NAME,NESTAB,NRCPTOT",
        "for": for_clause,
        "NAICS2017": naics_code,
        "key": API_KEY,
    }
    url = f"https://api.census.gov/data/{year}/nonemp"
    resp = session.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"  ERROR NAICS {naics_code}: HTTP {resp.status_code} - {resp.text[:300]}")
        return []
    rows = resp.json()
    header, *data_rows = rows
    return [dict(zip(header, row)) for row in data_rows]


def normalize(rows, year, naics_code):
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for r in rows:
        geo_name = r.get("NAME")
        records.append({
            "entity_id": f"census_nes:{year}:{naics_code}:{geo_name}",
            "source": "census_nes",
            "source_native_id": f"{year}-{naics_code}-{geo_name}",
            "entity_type": "aggregate_geo_sector",
            "name_or_title": f"{geo_name} - NAICS {naics_code} - {year}",
            "description_text": None,
            "url": f"https://data.census.gov/",
            "created_at": f"{year}-01-01",
            "retrieved_at": now,
            "geography": geo_name,
            "naics2017": naics_code,
            "year": year,
            "nonemployer_establishments": r.get("NESTAB"),
            "nonemployer_receipts_thousands": r.get("NRCPTOT"),
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2021,
                         help="anio del dataset NES (ver years disponibles en la API)")
    parser.add_argument("--naics", type=str, default=",".join(DEFAULT_NAICS),
                         help="codigos NAICS2017 de 2 digitos, separados por coma")
    parser.add_argument("--geo", choices=["us", "state"], default="state",
                         help="nivel geografico")
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit(
            "ERROR: falta CENSUS_API_KEY en .env. "
            "Registro gratis (email, sin captcha) en "
            "https://api.census.gov/data/key_signup.html"
        )

    session = requests.Session()
    naics_codes = [c.strip() for c in args.naics.split(",") if c.strip()]

    all_records = []
    for code in naics_codes:
        print(f"Sector NAICS {code}, geo={args.geo}, year={args.year}...")
        rows = fetch_naics(session, args.year, code, args.geo)
        recs = normalize(rows, args.year, code)
        print(f"  {len(recs)} registros")
        all_records.extend(recs)

    print(f"\nTotal registros: {len(all_records)}")

    out_dir = ROOT / "data" / "raw" / "census_nes"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"census_nes_{timestamp}.json"
    out_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
