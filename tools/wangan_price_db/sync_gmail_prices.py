#!/usr/bin/env python3
"""Sync wangan mansion listing emails from Gmail into a SQLite database."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import email.utils
import hashlib
import html
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DEFAULT_QUERY = '("湾岸" OR "豊洲" OR "晴海" OR "勝どき" OR "月島" OR "有明" OR "東雲") newer_than:14d'


@dataclass(frozen=True)
class GmailMessage:
    message_id: str
    thread_id: str
    received_at: str
    from_email: str
    subject: str
    snippet: str
    body_text: str


@dataclass(frozen=True)
class PriceObservation:
    observation_id: str
    message_id: str
    observed_at: str
    property_name: str | None
    area: str | None
    room_type: str | None
    floor: int | None
    size_sqm: float | None
    price_jpy: int
    unit_price_per_tsubo: int | None
    source_text: str
    confidence: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=getenv_default("WANGAN_DB_PATH", "data/wangan_prices.sqlite"))
    parser.add_argument("--query", default=getenv_default("WANGAN_GMAIL_QUERY", DEFAULT_QUERY))
    parser.add_argument("--max-results", type=int, default=int(getenv_default("WANGAN_GMAIL_MAX_RESULTS", "50")))
    parser.add_argument("--dry-run", action="store_true", help="Fetch and parse without writing to SQLite.")
    return parser.parse_args()


def getenv_default(name: str, default: str) -> str:
    return os.environ.get(name) or default


def build_gmail_service():
    required = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=[GMAIL_SCOPE],
    )
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS gmail_messages (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            received_at TEXT NOT NULL,
            from_email TEXT,
            subject TEXT,
            snippet TEXT,
            body_text TEXT,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS price_observations (
            observation_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL REFERENCES gmail_messages(message_id),
            observed_at TEXT NOT NULL,
            property_name TEXT,
            area TEXT,
            room_type TEXT,
            floor INTEGER,
            size_sqm REAL,
            price_jpy INTEGER NOT NULL,
            unit_price_per_tsubo INTEGER,
            source_text TEXT NOT NULL,
            confidence REAL NOT NULL,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_price_observations_observed_at
            ON price_observations(observed_at);

        CREATE INDEX IF NOT EXISTS idx_price_observations_property_name
            ON price_observations(property_name);
        """
    )


def search_message_ids(service, query: str, max_results: int) -> list[dict[str, str]]:
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    return response.get("messages", [])


def fetch_message(service, message_id: str) -> GmailMessage:
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    headers = {item["name"].lower(): item["value"] for item in message["payload"].get("headers", [])}
    subject = headers.get("subject", "")
    from_email = headers.get("from", "")
    received_at = parse_message_date(headers.get("date"), message.get("internalDate"))
    body_text = extract_text_from_payload(message["payload"])
    return GmailMessage(
        message_id=message["id"],
        thread_id=message.get("threadId", ""),
        received_at=received_at,
        from_email=from_email,
        subject=subject,
        snippet=message.get("snippet", ""),
        body_text=body_text,
    )


def parse_message_date(date_header: str | None, internal_date_ms: str | None) -> str:
    if date_header:
        parsed = email.utils.parsedate_to_datetime(date_header)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed.astimezone(dt.UTC).isoformat()
    if internal_date_ms:
        return dt.datetime.fromtimestamp(int(internal_date_ms) / 1000, tz=dt.UTC).isoformat()
    return dt.datetime.now(dt.UTC).isoformat()


def extract_text_from_payload(payload: dict) -> str:
    chunks: list[str] = []

    def walk(part: dict) -> None:
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        if data and mime_type in {"text/plain", "text/html"}:
            decoded = decode_body(data)
            if mime_type == "text/html":
                decoded = html_to_text(decoded)
            chunks.append(decoded)
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return normalize_text("\n".join(chunks))


def decode_body(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def html_to_text(value: str) -> str:
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(value)


def normalize_text(value: str) -> str:
    value = value.replace("\u3000", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


PRICE_RE = re.compile(r"(?P<price>\d{1,3}(?:,\d{3})+|\d{3,6})\s*(?:万円|万)")
TSUBO_RE = re.compile(r"(?:坪単価|坪)\s*[:：]?\s*(?P<unit>\d{2,4})\s*(?:万円|万)")
SIZE_RE = re.compile(r"(?P<size>\d{2,3}(?:\.\d+)?)\s*(?:m2|㎡|平米)")
FLOOR_RE = re.compile(r"(?P<floor>\d{1,2})\s*階")
ROOM_RE = re.compile(r"\b(?P<room>[1-5][SLDKR＋+]{1,6})\b", re.IGNORECASE)
AREA_RE = re.compile(r"(豊洲|晴海|勝どき|月島|有明|東雲|芝浦|港南|台場|湾岸)")
PROPERTY_HINT_RE = re.compile(
    r"(?P<name>[^\n。]{0,30}(?:タワー|レジデンス|マンション|シティ|パーク|ベイ|晴海フラッグ|HARUMI FLAG)[^\n。]{0,30})",
    re.IGNORECASE,
)


def extract_observations(message: GmailMessage) -> list[PriceObservation]:
    text = "\n".join(part for part in [message.subject, message.body_text] if part)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    observations: list[PriceObservation] = []

    for index, line in enumerate(lines):
        for match in PRICE_RE.finditer(line):
            price_jpy = parse_price_to_jpy(match.group("price"))
            if price_jpy < 10_000_000:
                continue
            context = build_context(lines, index)
            observation = build_observation(message, context, price_jpy)
            observations.append(observation)

    return dedupe_observations(observations)


def parse_price_to_jpy(value: str) -> int:
    normalized = value.replace(",", "")
    return int(normalized) * 10_000


def build_context(lines: list[str], index: int) -> str:
    start = max(index - 2, 0)
    end = min(index + 3, len(lines))
    return normalize_text("\n".join(lines[start:end]))


def build_observation(message: GmailMessage, context: str, price_jpy: int) -> PriceObservation:
    property_name = find_first(PROPERTY_HINT_RE, context, "name")
    area = find_first(AREA_RE, context, 1)
    room_type = find_first(ROOM_RE, context, "room")
    floor = parse_int(find_first(FLOOR_RE, context, "floor"))
    size_sqm = parse_float(find_first(SIZE_RE, context, "size"))
    unit_price = parse_int(find_first(TSUBO_RE, context, "unit"))
    confidence = score_confidence(property_name, area, room_type, size_sqm, unit_price)
    observation_id = stable_observation_id(message.message_id, context, price_jpy)
    return PriceObservation(
        observation_id=observation_id,
        message_id=message.message_id,
        observed_at=message.received_at,
        property_name=property_name,
        area=area,
        room_type=room_type.upper() if room_type else None,
        floor=floor,
        size_sqm=size_sqm,
        price_jpy=price_jpy,
        unit_price_per_tsubo=unit_price,
        source_text=context,
        confidence=confidence,
    )


def find_first(pattern: re.Pattern[str], value: str, group: str | int) -> str | None:
    match = pattern.search(value)
    if not match:
        return None
    return normalize_text(match.group(group))


def parse_int(value: str | None) -> int | None:
    return int(value) if value else None


def parse_float(value: str | None) -> float | None:
    return float(value) if value else None


def score_confidence(
    property_name: str | None,
    area: str | None,
    room_type: str | None,
    size_sqm: float | None,
    unit_price: int | None,
) -> float:
    score = 0.35
    score += 0.2 if property_name else 0
    score += 0.15 if area else 0
    score += 0.1 if room_type else 0
    score += 0.1 if size_sqm else 0
    score += 0.1 if unit_price else 0
    return min(score, 1.0)


def stable_observation_id(message_id: str, context: str, price_jpy: int) -> str:
    digest = hashlib.sha256(f"{message_id}|{price_jpy}|{context}".encode("utf-8")).hexdigest()
    return digest[:32]


def dedupe_observations(observations: Iterable[PriceObservation]) -> list[PriceObservation]:
    deduped: dict[str, PriceObservation] = {}
    for observation in observations:
        deduped[observation.observation_id] = observation
    return list(deduped.values())


def save_message(conn: sqlite3.Connection, message: GmailMessage) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO gmail_messages (
            message_id, thread_id, received_at, from_email, subject, snippet, body_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message.message_id,
            message.thread_id,
            message.received_at,
            message.from_email,
            message.subject,
            message.snippet,
            message.body_text,
        ),
    )


def save_observations(conn: sqlite3.Connection, observations: Iterable[PriceObservation]) -> int:
    count = 0
    for observation in observations:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO price_observations (
                observation_id,
                message_id,
                observed_at,
                property_name,
                area,
                room_type,
                floor,
                size_sqm,
                price_jpy,
                unit_price_per_tsubo,
                source_text,
                confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation.observation_id,
                observation.message_id,
                observation.observed_at,
                observation.property_name,
                observation.area,
                observation.room_type,
                observation.floor,
                observation.size_sqm,
                observation.price_jpy,
                observation.unit_price_per_tsubo,
                observation.source_text,
                observation.confidence,
            ),
        )
        count += cursor.rowcount
    return count


def main() -> None:
    args = parse_args()
    service = build_gmail_service()
    message_refs = search_message_ids(service, args.query, args.max_results)
    print(f"Found {len(message_refs)} Gmail messages for query: {args.query}")

    db_path = Path(args.db)
    if not args.dry_run:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = None if args.dry_run else sqlite3.connect(db_path)
    if conn:
        init_db(conn)

    imported_messages = 0
    imported_observations = 0
    for ref in message_refs:
        message = fetch_message(service, ref["id"])
        observations = extract_observations(message)
        print(
            f"{message.received_at} | {message.subject[:80]} | "
            f"{len(observations)} price observations"
        )
        if conn:
            save_message(conn, message)
            imported_messages += 1
            imported_observations += save_observations(conn, observations)

    if conn:
        conn.commit()
        conn.close()

    print(
        f"Done. Imported messages: {imported_messages}. "
        f"New price observations: {imported_observations}."
    )


if __name__ == "__main__":
    main()
