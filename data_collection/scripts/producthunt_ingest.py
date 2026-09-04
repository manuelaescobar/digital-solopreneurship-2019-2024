#!/usr/bin/env python3
"""
Ingesta de Product Hunt via API GraphQL oficial (v2).

Fuente 100% compatible con ToS: usamos el endpoint publico documentado,
no scraping. Requiere PRODUCTHUNT_TOKEN en .env (ver README.md).

Recupera posts publicados en una ventana de dias, con sus makers, topics
y metricas, y aplica la heuristica de etiquetado v1 (ver
schema/definicion_operativa.md) para marcar candidatos a solopreneur.

Uso:
    python3 producthunt_ingest.py --days 30
    python3 producthunt_ingest.py --days 30 --topics saas,no-code,productivity
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_URL = "https://api.producthunt.com/v2/api/graphql"
TOKEN = os.getenv("PRODUCTHUNT_TOKEN")

QUERY = """
query Posts($after: String, $postedAfter: DateTime, $postedBefore: DateTime) {
  posts(first: 50, after: $after, postedAfter: $postedAfter, postedBefore: $postedBefore, order: NEWEST) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        name
        tagline
        description
        url
        website
        votesCount
        commentsCount
        createdAt
        topics(first: 10) { edges { node { name } } }
        makers { id name username twitterUsername }
      }
    }
  }
}
"""

# Heuristica de etiquetado v1 (deliberadamente ruidosa, ver
# schema/definicion_operativa.md). Se aplica sobre tagline+description.
INTENTIONAL_KEYWORDS = [
    "bootstrapped", "bootstrap", "solo founder", "solo-founder", "one-person",
    "one person", "built by one", "indie", "lifestyle business", "staying small",
    "no vc", "self-funded", "built solo",
]
LEVERAGE_NEGATIVE_KEYWORDS = [
    "consulting", "agency services", "freelance services", "hire me",
    "book a call to hire", "staffing",
]


def label_record(tagline: str, description: str, maker_count: int) -> dict:
    text = f"{tagline or ''} {description or ''}".lower()
    structural = (maker_count == 1) if maker_count is not None else None
    intentional = any(kw in text for kw in INTENTIONAL_KEYWORDS) or None
    leverage = True
    if any(kw in text for kw in LEVERAGE_NEGATIVE_KEYWORDS):
        leverage = False
    is_candidate = bool(structural) and bool(intentional) and bool(leverage)
    return {
        "structural_signal": structural,
        "intentional_signal": intentional,
        "leverage_signal": leverage,
        "is_solopreneur_candidate": is_candidate,
        "labeling_method": "keyword_heuristic_v1",
    }


def _is_rate_limited(response):
    return response is not None and response.status_code == 429


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_result(_is_rate_limited),
)
def _post(session, variables):
    resp = session.post(
        API_URL,
        json={"query": QUERY, "variables": variables},
        timeout=30,
    )
    return resp


def fetch_posts(days: int):
    if not TOKEN:
        sys.exit(
            "ERROR: falta PRODUCTHUNT_TOKEN en .env. "
            "Ver README.md -> Setup -> Product Hunt."
        )

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })

    posted_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    after_cursor = None
    all_nodes = []
    page = 0

    while True:
        variables = {"after": after_cursor, "postedAfter": posted_after}
        resp = _post(session, variables)

        if resp.status_code != 200:
            print(f"ERROR HTTP {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            break

        payload = resp.json()
        if "errors" in payload:
            print(f"ERROR GraphQL: {payload['errors']}", file=sys.stderr)
            break

        posts = payload["data"]["posts"]
        edges = posts["edges"]
        all_nodes.extend(e["node"] for e in edges)
        page += 1
        print(f"  pagina {page}: +{len(edges)} posts (total {len(all_nodes)})")

        if not posts["pageInfo"]["hasNextPage"] or not edges:
            break
        after_cursor = posts["pageInfo"]["endCursor"]

        # Cortesia con el rate limit de la API (complexity-based, ~6250 pts/15min)
        time.sleep(1.0)

    return all_nodes


def normalize(nodes):
    records = []
    now = datetime.now(timezone.utc).isoformat()
    for n in nodes:
        maker_count = len(n.get("makers") or [])
        topics = [t["node"]["name"] for t in (n.get("topics", {}).get("edges") or [])]
        labels = label_record(n.get("tagline"), n.get("description"), maker_count)
        records.append({
            "entity_id": f"producthunt:{n['id']}",
            "source": "producthunt",
            "source_native_id": n["id"],
            "entity_type": "product",
            "name_or_title": n.get("name"),
            "description_text": n.get("tagline"),
            "description_long": n.get("description"),
            "url": n.get("url"),
            "website": n.get("website"),
            "created_at": n.get("createdAt"),
            "retrieved_at": now,
            "maker_count": maker_count,
            "makers": n.get("makers"),
            "metric_primary": n.get("votesCount"),
            "metric_secondary": n.get("commentsCount"),
            "category_raw": topics,
            **labels,
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30,
                         help="ventana de dias hacia atras a recolectar")
    args = parser.parse_args()

    print(f"Recolectando posts de Product Hunt de los ultimos {args.days} dias...")
    nodes = fetch_posts(args.days)
    records = normalize(nodes)

    candidates = sum(1 for r in records if r["is_solopreneur_candidate"])
    print(f"Total posts: {len(records)} | candidatos solopreneur (heuristica v1): {candidates}")

    out_dir = ROOT / "data" / "raw" / "producthunt"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"producthunt_{timestamp}.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
