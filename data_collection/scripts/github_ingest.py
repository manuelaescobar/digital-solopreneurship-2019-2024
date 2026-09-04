#!/usr/bin/env python3
"""
Ingesta de GitHub Search API (abierta; funciona sin token con rate limit
bajo de 10 req/min, o con un Personal Access Token propio para 30 req/min
- generado en tu propia cuenta en Settings > Developer settings >
Personal access tokens, sin registro de app ni captcha).

Busca repos por topics/keywords relacionados a solopreneurship digital
(indie hacker, microsaas, solo founder, bootstrapped, buildinpublic) como
proxy de actividad de desarrollo solo.

Uso:
    python3 github_ingest.py
    GITHUB_TOKEN=ghp_xxx python3 github_ingest.py --max-results 500
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_URL = "https://api.github.com/search/repositories"
TOKEN = os.getenv("GITHUB_TOKEN")

DEFAULT_QUERIES = [
    "topic:indie-hacker",
    "topic:solopreneur",
    "topic:microsaas",
    "topic:buildinpublic",
    "topic:bootstrapped",
    "topic:saas topic:solo",
    "topic:one-person-business",
    "topic:side-project",
    "topic:no-code",
]


def fetch_query(session, query, max_results):
    results = []
    page = 1
    per_page = 100
    while len(results) < max_results:
        params = {"q": query, "per_page": per_page, "page": page, "sort": "updated"}
        resp = session.get(API_URL, params=params, timeout=30)
        if resp.status_code == 403:
            reset = resp.headers.get("X-RateLimit-Reset")
            print(f"  rate limit alcanzado, esperando... (reset epoch {reset})")
            time.sleep(15)
            continue
        if resp.status_code != 200:
            print(f"  ERROR HTTP {resp.status_code} para '{query}': {resp.text[:300]}")
            break
        payload = resp.json()
        items = payload.get("items", [])
        results.extend(items)
        print(f"  '{query}': +{len(items)} (total {len(results)} de {payload.get('total_count')} disponibles)")
        if len(items) < per_page or page >= 10:  # GitHub Search API limita a 1000 resultados (10 paginas x 100)
            break
        page += 1
        time.sleep(2.5 if not TOKEN else 1.0)  # cortesia con rate limit sin token
    return results[:max_results]


def normalize(items, query_used):
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for it in items:
        records.append({
            "entity_id": f"github:{it['id']}",
            "source": "github",
            "source_native_id": str(it["id"]),
            "entity_type": "repository",
            "name_or_title": it.get("full_name"),
            "description_text": it.get("description"),
            "url": it.get("html_url"),
            "created_at": it.get("created_at"),
            "retrieved_at": now,
            "author_handle": (it.get("owner") or {}).get("login"),
            "owner_type": (it.get("owner") or {}).get("type"),  # User vs Organization -> proxy de "solo"
            "metric_primary": it.get("stargazers_count"),
            "metric_secondary": it.get("forks_count"),
            "language": it.get("language"),
            "topics": it.get("topics"),
            "matched_query": query_used,
            "structural_signal": ((it.get("owner") or {}).get("type") == "User") or None,
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--max-results", type=int, default=300)
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"Accept": "application/vnd.github+json"})
    if TOKEN:
        session.headers.update({"Authorization": f"Bearer {TOKEN}"})
    else:
        print("Aviso: sin GITHUB_TOKEN en .env -> rate limit bajo (10 req/min). "
              "Un token personal (no requiere app ni captcha) lo sube a 30 req/min.")

    queries = [args.query] if args.query else DEFAULT_QUERIES
    all_records = []
    for q in queries:
        print(f"Buscando: {q}")
        items = fetch_query(session, q, args.max_results)
        all_records.extend(normalize(items, q))

    dedup = {r["entity_id"]: r for r in all_records}
    records = list(dedup.values())
    print(f"\nTotal repos unicos: {len(records)}")

    out_dir = ROOT / "data" / "raw" / "github"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"github_{timestamp}.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
