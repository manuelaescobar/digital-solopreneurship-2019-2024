#!/usr/bin/env python3
"""
Ingesta de Reddit via API oficial (PRAW). Fuente 100% compatible con ToS.

Recolecta submissions (+ un top-N de comentarios de cada una) de los
subreddits objetivo, y aplica la heuristica de etiquetado v1
(ver schema/definicion_operativa.md).

Limitacion conocida: la API de Reddit solo expone ~1000 items por listado
(new/top/hot), independientemente del cliente usado. Para backfill
historico masivo, la via es el dump de Academic Torrents (Reddit
submissions/comments completos por subreddit, no requiere API) - queda
como tarea aparte, no cubierta por este script.

Uso:
    python3 reddit_ingest.py --limit 500
    python3 reddit_ingest.py --limit 500 --subreddits solopreneur,indiehackers
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import praw
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DEFAULT_SUBREDDITS = [
    "solopreneur", "indiehackers", "SaaS", "microsaas", "SideProject",
    "EntrepreneurRideAlong",
]

INTENTIONAL_KEYWORDS = [
    "bootstrapped", "bootstrap", "solo founder", "solo-founder", "one-person",
    "one person", "just me", "no employees", "built by one", "indie",
    "lifestyle business", "staying small", "no vc", "self-funded",
]
LEVERAGE_NEGATIVE_KEYWORDS = [
    "consulting", "agency services", "freelance services", "hire me",
    "staffing",
]


def label_record(title: str, body: str) -> dict:
    text = f"{title or ''} {body or ''}".lower()
    structural = any(kw in text for kw in [
        "solo founder", "solo-founder", "just me", "one-person", "one person",
        "no employees", "no co-founder",
    ]) or None
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


def get_client():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    if not all([client_id, client_secret, user_agent]):
        sys.exit(
            "ERROR: faltan credenciales de Reddit en .env. "
            "Ver README.md -> Setup -> Reddit."
        )
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def normalize_submission(sub, now):
    labels = label_record(sub.title, sub.selftext)
    return {
        "entity_id": f"reddit:{sub.id}",
        "source": "reddit",
        "source_native_id": sub.id,
        "entity_type": "post",
        "subreddit": str(sub.subreddit),
        "name_or_title": sub.title,
        "description_text": sub.selftext,
        "url": f"https://www.reddit.com{sub.permalink}",
        "external_link": sub.url if not sub.is_self else None,
        "created_at": datetime.fromtimestamp(sub.created_utc, tz=timezone.utc).isoformat(),
        "retrieved_at": now,
        "author_handle": str(sub.author) if sub.author else None,
        "metric_primary": sub.score,
        "metric_secondary": sub.num_comments,
        "flair": sub.link_flair_text,
        **labels,
    }


def normalize_comment(comment, parent_id, now):
    labels = label_record("", comment.body)
    return {
        "entity_id": f"reddit:{comment.id}",
        "source": "reddit",
        "source_native_id": comment.id,
        "entity_type": "comment",
        "parent_entity_id": parent_id,
        "name_or_title": None,
        "description_text": comment.body,
        "url": f"https://www.reddit.com{comment.permalink}",
        "created_at": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
        "retrieved_at": now,
        "author_handle": str(comment.author) if comment.author else None,
        "metric_primary": comment.score,
        "metric_secondary": None,
        **labels,
    }


def fetch_subreddit(reddit, name, limit, top_comments_per_post=5):
    print(f"  r/{name} ...")
    now = datetime.now(timezone.utc).isoformat()
    records = []
    subreddit = reddit.subreddit(name)
    for sub in subreddit.new(limit=limit):
        records.append(normalize_submission(sub, now))
        try:
            sub.comments.replace_more(limit=0)
            for c in sub.comments[:top_comments_per_post]:
                records.append(normalize_comment(c, f"reddit:{sub.id}", now))
        except Exception as e:
            print(f"    aviso: no se pudieron traer comentarios de {sub.id}: {e}", file=sys.stderr)
    print(f"    {len(records)} registros (posts + comentarios)")
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500,
                         help="max submissions por subreddit (tope real de la API ~1000)")
    parser.add_argument("--subreddits", type=str, default=",".join(DEFAULT_SUBREDDITS),
                         help="lista separada por comas")
    args = parser.parse_args()

    reddit = get_client()
    subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]

    print(f"Recolectando de {len(subreddits)} subreddits (limite {args.limit} c/u)...")
    all_records = []
    for name in subreddits:
        all_records.extend(fetch_subreddit(reddit, name, args.limit))

    candidates = sum(1 for r in all_records if r.get("is_solopreneur_candidate"))
    print(f"Total registros: {len(all_records)} | candidatos solopreneur (heuristica v1): {candidates}")

    out_dir = ROOT / "data" / "raw" / "reddit"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"reddit_{timestamp}.json"
    out_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
