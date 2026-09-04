#!/usr/bin/env python3
"""
Ingesta de World Bank Open Data (API abierta, sin key ni registro).

Trae series pais-anio de autoempleo, para el contexto macro del modelo
multinivel (ver Capa 6 de la propuesta de fuentes).

Indicadores por defecto:
  SL.EMP.SELF.ZS    - Self-employed, total (% of total employment)
  SL.EMP.SELF.MA.ZS - Self-employed, male (%)
  SL.EMP.SELF.FE.ZS - Self-employed, female (%)
  SL.EMP.VULN.ZS    - Vulnerable employment, total (% of total employment)
  IT.NET.USER.ZS    - Individuals using the Internet (% of population)

Uso:
    python3 worldbank_ingest.py
    python3 worldbank_ingest.py --indicators SL.EMP.SELF.ZS,IT.NET.USER.ZS --start 2010 --end 2024
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}"

DEFAULT_INDICATORS = {
    "SL.EMP.SELF.ZS": "self_employed_pct_total",
    "SL.EMP.SELF.MA.ZS": "self_employed_pct_male",
    "SL.EMP.SELF.FE.ZS": "self_employed_pct_female",
    "SL.EMP.VULN.ZS": "vulnerable_employment_pct",
    "IT.NET.USER.ZS": "internet_users_pct",
}


def fetch_indicator(session, indicator_code, start, end):
    page = 1
    all_rows = []
    while True:
        params = {
            "format": "json",
            "per_page": 1000,
            "date": f"{start}:{end}",
            "page": page,
        }
        resp = session.get(API_URL.format(indicator=indicator_code), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  ERROR HTTP {resp.status_code} para {indicator_code}")
            break
        payload = resp.json()
        if not payload or len(payload) < 2 or payload[1] is None:
            break
        meta, rows = payload[0], payload[1]
        all_rows.extend(rows)
        if page >= meta.get("pages", 1):
            break
        page += 1
        time.sleep(0.2)
    return all_rows


def normalize(rows, indicator_code, field_name):
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for r in rows:
        if r.get("value") is None:
            continue
        country = r.get("country", {})
        # countryiso3code viene vacio para agregados regionales/de ingreso
        # (ej. "High income", "Low income") -> usar el id interno del WB
        # como respaldo para no colapsar geografias distintas bajo el mismo id.
        geo_code = r.get("countryiso3code") or country.get("id") or country.get("value")
        records.append({
            "entity_id": f"worldbank:{indicator_code}:{geo_code}:{r.get('date')}",
            "source": "worldbank",
            "source_native_id": f"{indicator_code}-{geo_code}-{r.get('date')}",
            "entity_type": "aggregate_country_year",
            "name_or_title": f"{country.get('value')} - {field_name} - {r.get('date')}",
            "description_text": None,
            "url": f"https://data.worldbank.org/indicator/{indicator_code}",
            "created_at": f"{r.get('date')}-01-01",
            "retrieved_at": now,
            "country_iso3": r.get("countryiso3code") or None,
            "country_name": country.get("value"),
            "is_aggregate": not bool(r.get("countryiso3code")),
            "year": r.get("date"),
            "indicator_code": indicator_code,
            "indicator_field": field_name,
            "value": r.get("value"),
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indicators", type=str, default=None,
                         help="codigos separados por coma; por defecto usa el set predefinido")
    parser.add_argument("--start", type=int, default=2005)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()

    if args.indicators:
        indicators = {code.strip(): code.strip() for code in args.indicators.split(",")}
    else:
        indicators = DEFAULT_INDICATORS

    session = requests.Session()
    all_records = []
    for code, field_name in indicators.items():
        print(f"Indicador {code} ({field_name}), {args.start}-{args.end}...")
        rows = fetch_indicator(session, code, args.start, args.end)
        recs = normalize(rows, code, field_name)
        print(f"  {len(recs)} observaciones pais-anio")
        all_records.extend(recs)

    print(f"\nTotal registros: {len(all_records)}")

    out_dir = ROOT / "data" / "raw" / "worldbank"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"worldbank_{timestamp}.json"
    out_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
