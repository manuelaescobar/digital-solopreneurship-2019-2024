#!/usr/bin/env python3
"""
Ingesta de Eurostat (API abierta, sin key ni registro).

Dataset por defecto: lfsa_esgais - "Self-employed persons by occupation",
que incluye la dimension wstatus con la categoria SELF_NS = "Self-employed
persons without employees (own-account workers)" - la variable ancla de
la definicion operativa (ver schema/definicion_operativa.md).

Uso:
    python3 eurostat_ingest.py
    python3 eurostat_ingest.py --dataset lfsa_esgais --wstatus SELF_NS --sex T --age Y_GE15
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"


def decode_jsonstat(payload):
    """Decodifica una respuesta JSON-stat 2.0 de Eurostat a filas planas."""
    dim_ids = payload["id"]
    sizes = payload["size"]
    dims = payload["dimension"]

    # Para cada dimension: lista ordenada de (codigo, etiqueta) por posicion
    dim_categories = []
    for dim_id in dim_ids:
        cat = dims[dim_id]["category"]
        index = cat["index"]
        label = cat.get("label", {})
        # index puede ser dict {codigo: pos} o lista [codigo,...]
        if isinstance(index, dict):
            ordered = sorted(index.items(), key=lambda kv: kv[1])
            codes = [code for code, _ in ordered]
        else:
            codes = list(index)
        dim_categories.append([(code, label.get(code, code)) for code in codes])

    values = payload.get("value", {})
    rows = []
    for flat_key, value in values.items():
        idx = int(flat_key)
        coords = []
        remainder = idx
        for size in reversed(sizes):
            coords.insert(0, remainder % size)
            remainder //= size
        row = {}
        for dim_id, pos, categories in zip(dim_ids, coords, dim_categories):
            code, label = categories[pos]
            row[dim_id] = code
            row[f"{dim_id}_label"] = label
        row["value"] = value
        rows.append(row)
    return rows


def fetch(dataset, filters):
    params = {"format": "JSON"}
    params.update(filters)
    resp = requests.get(BASE_URL.format(dataset=dataset), params=params, timeout=60)
    if resp.status_code != 200:
        raise SystemExit(f"ERROR HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def normalize(rows, dataset):
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for r in rows:
        geo = r.get("geo")
        time_ = r.get("time")
        records.append({
            "entity_id": f"eurostat:{dataset}:{geo}:{time_}:{r.get('wstatus','')}:{r.get('sex','')}:{r.get('age','')}:{r.get('isco08','')}",
            "source": "eurostat",
            "source_native_id": f"{dataset}-{geo}-{time_}",
            "entity_type": "aggregate_country_year",
            "name_or_title": f"{r.get('geo_label')} - {r.get('wstatus_label')} - {time_}",
            "description_text": None,
            "url": f"https://ec.europa.eu/eurostat/databrowser/view/{dataset}",
            "created_at": f"{time_}-01-01" if time_ else None,
            "retrieved_at": now,
            "country_code": geo,
            "country_name": r.get("geo_label"),
            "year": time_,
            "work_status": r.get("wstatus"),
            "work_status_label": r.get("wstatus_label"),
            "sex": r.get("sex"),
            "age_group": r.get("age"),
            "occupation": r.get("isco08_label"),
            "unit": r.get("unit_label"),
            "value_thousands": r.get("value"),
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="lfsa_esgais")
    parser.add_argument("--wstatus", default="SELF_NS",
                         help="SELF_NS=sin empleados (own-account), SELF_S=con empleados, SELF=total")
    parser.add_argument("--sex", default="T", help="T=total, M=hombres, F=mujeres")
    parser.add_argument("--age", default="Y_GE15")
    parser.add_argument("--isco08", default="TOTAL",
                         help="TOTAL=todas las ocupaciones agregadas (evita duplicar filas por ocupacion)")
    parser.add_argument("--start", type=int, default=2015)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()

    filters = {
        "wstatus": args.wstatus,
        "sex": args.sex,
        "age": args.age,
        "isco08": args.isco08,
    }
    all_rows = []
    for year in range(args.start, args.end + 1):
        print(f"Anio {year}...")
        try:
            payload = fetch(args.dataset, {**filters, "time": year})
        except SystemExit as e:
            print(f"  {e}")
            continue
        rows = decode_jsonstat(payload)
        print(f"  {len(rows)} paises")
        all_rows.extend(rows)

    records = normalize(all_rows, args.dataset)
    print(f"\nTotal registros: {len(records)}")

    out_dir = ROOT / "data" / "raw" / "eurostat"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"eurostat_{timestamp}.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
