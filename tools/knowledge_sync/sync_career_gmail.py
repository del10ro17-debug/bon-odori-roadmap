#!/usr/bin/env python3
"""Fetch career / job-search Gmail into Obsidian .raw/ for auto-ingest."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "wangan_price_db"))

from sync_gmail_prices import build_gmail_service, fetch_message, search_message_ids

VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian"
RAW_DIR = VAULT / ".raw"
STATE_FILE = VAULT / "wiki/.career-gmail-sync-state.json"

DEFAULT_QUERY = (
    "(from:makenotion.com OR from:ashbyhq.com OR from:jobs.mail.notion.so "
    'OR subject:"Notion Confirmation" OR subject:"Sales Manager" OR label:転職活動) '
    "newer_than:90d"
)

ENV_FILES = [
    Path.home() / "Projects/wangan-db/.env",
    Path.home() / ".claude/obsidian-sync.env",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=os.environ.get("CAREER_GMAIL_QUERY", DEFAULT_QUERY))
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_dotenv() -> None:
    for env_path in ENV_FILES:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"processedIds": [], "lastRun": None}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value: str, limit: int = 48) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return (value or "message")[:limit]


def sender_slug(from_email: str) -> str:
    match = re.search(r"[\w.+-]+@([\w.-]+)", from_email)
    domain = match.group(1) if match else "unknown"
    domain = domain.replace("makenotion.com", "notion").replace("ashbyhq.com", "ashby")
    return slugify(domain.split(".")[0])


def received_date(iso_ts: str) -> str:
    parsed = dt.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return parsed.astimezone(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d")


def build_raw_markdown(message) -> str:
    date = received_date(message.received_at)
    body = (message.body_text or message.snippet or "").strip()
    if len(body) > 12000:
        body = body[:12000] + "\n\n... [truncated]"

    title = message.subject.strip() or "Career email"
    return f"""---
source: Gmail
message_id: {message.message_id}
date: {date}
category: 転職活動
tags: [email, 転職活動]
from: {message.from_email}
subject: {json.dumps(title, ensure_ascii=False)}
---

# {title}

**送信者**: {message.from_email}  
**件名**: {message.subject}  
**日時**: {message.received_at}

## 本文

{body}
"""


def output_path(message) -> Path:
    date = received_date(message.received_at)
    slug = sender_slug(message.from_email)
    subject_slug = slugify(message.subject, limit=32)
    return RAW_DIR / f"email-{slug}-{date}-{subject_slug}.md"


def main() -> int:
    args = parse_args()
    load_dotenv()

    state = load_state()
    processed = set(state.get("processedIds") or [])

    service = build_gmail_service()
    refs = search_message_ids(service, args.query, args.max_results)
    if not refs:
        print(f"No messages matched: {args.query}")
        state["lastRun"] = dt.datetime.now(dt.UTC).isoformat()
        if not args.dry_run:
            save_state(state)
        return 0

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0

    for ref in refs:
        message_id = ref["id"]
        if message_id in processed:
            skipped += 1
            continue

        message = fetch_message(service, message_id)
        out = output_path(message)

        if out.exists():
            print(f"skip exists: {out.name}")
            processed.add(message_id)
            skipped += 1
            continue

        print(f"{'[dry-run] ' if args.dry_run else ''}write: {out.name}")
        if not args.dry_run:
            out.write_text(build_raw_markdown(message), encoding="utf-8")
            processed.add(message_id)
            created += 1

    state["processedIds"] = sorted(processed)[-500:]
    state["lastRun"] = dt.datetime.now(dt.UTC).isoformat()
    if not args.dry_run:
        save_state(state)

    print(f"done: created={created} skipped={skipped} query={args.query!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
