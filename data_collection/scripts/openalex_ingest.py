#!/usr/bin/env python3
"""
Ingesta de OpenAlex (API abierta, sin autenticacion) para el mapeo
bibliometrico del campo de solopreneurship / self-employment digital.

Uso:
    python3 openalex_ingest.py
    python3 openalex_ingest.py --query "solopreneur OR \"solo entrepreneur\""
    python3 openalex_ingest.py --query "\"one-person business\"" --max-results 2000
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.openalex.org/works"

DEFAULT_QUERIES = [
    "solopreneur",
    '"solo entrepreneur"',
    '"one-person business"',
    '"own-account worker"',
    '"digital nomad entrepreneur"',
    '"indie hacker"',
]

# OpenAlex pide identificarse via 'mailto' en el user-agent/param para el
# pool de cortesia (mayor rate limit, sin necesidad de API key).
POLITE_EMAIL = "manuelaescobar@gmail.com"


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return None
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def fetch_query(session, query, max_results):
    results = []
    cursor = "*"
    while len(results) < max_results:
        params = {
            "search": query,
            "per-page": 200,
            "cursor": cursor,
            "mailto": POLITE_EMAIL,
        }
        resp = session.get(API_URL, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  ERROR HTTP {resp.status_code} para query '{query}': {resp.text[:300]}")
            break
        payload = resp.json()
        batch = payload["results"]
        results.extend(batch)
        cursor = payload.get("meta", {}).get("next_cursor")
        print(f"  '{query}': +{len(batch)} (total {len(results)}, de {payload['meta']['count']} disponibles)")
        if not cursor or not batch:
            break
        time.sleep(0.2)
    return results[:max_results]


def normalize(works, query_used):
    now = datetime.now(timezone.utc).isoformat()
    records = []
    seen_ids = set()
    for w in works:
        oa_id = w["id"]
        if oa_id in seen_ids:
            continue
        seen_ids.add(oa_id)
        authors = [
            a["author"]["display_name"]
            for a in w.get("authorships", [])
            if a.get("author")
        ]
        concepts = [c["display_name"] for c in w.get("concepts", [])[:10]]
        records.append({
            "entity_id": f"openalex:{oa_id.rsplit('/', 1)[-1]}",
            "source": "openalex",
            "source_native_id": oa_id,
            "entity_type": "paper",
            "name_or_title": w.get("display_name"),
            "description_text": reconstruct_abstract(w.get("abstract_inverted_index")),
            "url": w.get("doi") or oa_id,
            "created_at": w.get("publication_date"),
            "retrieved_at": now,
            "authors": authors,
            "metric_primary": w.get("cited_by_count"),
            "metric_secondary": None,
            "category_raw": concepts,
            "venue": (w.get("primary_location") or {}).get("source", {}).get("display_name")
                     if (w.get("primary_location") or {}).get("source") else None,
            "matched_query": query_used,
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None,
                         help="query unica; si se omite usa el set por defecto")
    parser.add_argument("--max-results", type=int, default=1000,
                         help="tope de resultados por query")
    args = parser.parse_args()

    queries = [args.query] if args.query else DEFAULT_QUERIES
    session = requests.Session()

    all_records = []
    for q in queries:
        print(f"Buscando: {q}")
        works = fetch_query(session, q, args.max_results)
        all_records.extend(normalize(works, q))

    # Deduplicar entre queries por entity_id
    dedup = {r["entity_id"]: r for r in all_records}
    records = list(dedup.values())
    print(f"\nTotal papers unicos: {len(records)}")

    out_dir = ROOT / "data" / "raw" / "openalex"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"openalex_{timestamp}.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
