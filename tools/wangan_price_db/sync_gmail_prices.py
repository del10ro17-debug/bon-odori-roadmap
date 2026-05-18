#!/usr/bin/env python3
"""Sync wangan mansion listing emails from Gmail into a SQLite database."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DEFAULT_QUERY = 'subject:"湾岸マンション価格ナビ" newer_than:180d'


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
class EmailLine:
    line_id: str
    message_id: str
    line_index: int
    line_text: str
    line_hash: str


@dataclass(frozen=True)
class PriceObservation:
    observation_id: str
    message_id: str
    observed_at: str
    source_type: str
    row_index: int
    property_name: str | None
    building_name: str | None
    project_name: str | None
    village_name: str | None
    building_code: str | None
    area: str | None
    room_type: str | None
    floor: int | None
    size_sqm: float | None
    price_jpy: int
    previous_price_jpy: int | None
    price_change_jpy: int | None
    unit_price_per_tsubo_man: float | None
    unit_price_per_tsubo_jpy: int | None
    direction: str | None
    raw_line: str
    source_text: str
    parsed_fields_json: str
    confidence: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=getenv_default("WANGAN_DB_PATH", "data/wangan_prices.sqlite"))
    parser.add_argument("--query", default=getenv_default("WANGAN_GMAIL_QUERY", DEFAULT_QUERY))
    parser.add_argument("--max-results", type=int, default=int(getenv_default("WANGAN_GMAIL_MAX_RESULTS", "500")))
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

        CREATE TABLE IF NOT EXISTS email_lines (
            line_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL REFERENCES gmail_messages(message_id),
            line_index INTEGER NOT NULL,
            line_text TEXT NOT NULL,
            line_hash TEXT NOT NULL,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(message_id, line_index)
        );

        CREATE TABLE IF NOT EXISTS price_observations (
            observation_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL REFERENCES gmail_messages(message_id),
            observed_at TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'price_context',
            row_index INTEGER,
            property_name TEXT,
            building_name TEXT,
            project_name TEXT,
            village_name TEXT,
            building_code TEXT,
            area TEXT,
            room_type TEXT,
            floor INTEGER,
            size_sqm REAL,
            price_jpy INTEGER NOT NULL,
            previous_price_jpy INTEGER,
            price_change_jpy INTEGER,
            unit_price_per_tsubo INTEGER,
            unit_price_per_tsubo_man REAL,
            unit_price_per_tsubo_jpy INTEGER,
            direction TEXT,
            raw_line TEXT,
            source_text TEXT NOT NULL,
            parsed_fields_json TEXT NOT NULL DEFAULT '{}',
            confidence REAL NOT NULL,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_email_lines_message_id
            ON email_lines(message_id);

        CREATE INDEX IF NOT EXISTS idx_price_observations_observed_at
            ON price_observations(observed_at);

        CREATE INDEX IF NOT EXISTS idx_price_observations_property_name
            ON price_observations(property_name);

        CREATE INDEX IF NOT EXISTS idx_price_observations_project_name
            ON price_observations(project_name);
        """
    )
    migrate_price_observations(conn)


def migrate_price_observations(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(price_observations)")}
    additions = {
        "source_type": "TEXT NOT NULL DEFAULT 'price_context'",
        "row_index": "INTEGER",
        "building_name": "TEXT",
        "project_name": "TEXT",
        "village_name": "TEXT",
        "building_code": "TEXT",
        "previous_price_jpy": "INTEGER",
        "price_change_jpy": "INTEGER",
        "unit_price_per_tsubo_man": "REAL",
        "unit_price_per_tsubo_jpy": "INTEGER",
        "direction": "TEXT",
        "raw_line": "TEXT",
        "parsed_fields_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE price_observations ADD COLUMN {column} {ddl}")
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_price_observations_project_name
            ON price_observations(project_name)
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
TSUBO_RE = re.compile(r"(?:坪単価|坪)?\s*[:：]?\s*(?P<unit>\d{2,4}(?:\.\d+)?)\s*(?:万円|万)")
SIZE_RE = re.compile(r"(?P<size>\d{2,3}(?:\.\d+)?)\s*(?:m2|㎡|平米)")
FLOOR_RE = re.compile(r"(?P<floor>\d{1,2})\s*階")
ROOM_RE = re.compile(r"\b(?P<room>[1-5][SLDKR＋+]{1,6})\b", re.IGNORECASE)
AREA_RE = re.compile(r"(豊洲|晴海|勝どき|月島|有明|東雲|芝浦|港南|台場|湾岸)")
DIRECTION_RE = re.compile(r"(北西|北東|南西|南東|北|南|東|西)(?:向き)?")
PRICE_CHANGE_RE = re.compile(r"(?P<sign>[▼▲△▽-])\s*(?P<amount>\d{1,3}(?:,\d{3})+|\d{2,6})\s*(?:万円|万)")
HARUMI_FLAG_RE = re.compile(r"(HARUMI\s*FLAG|晴海フラッグ)", re.IGNORECASE)
BUILDING_CODE_RE = re.compile(r"(?:^|[^A-Z0-9])(?P<code>[A-Z])\s*棟", re.IGNORECASE)
FULLWIDTH_ASCII_TRANS = str.maketrans(
    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
)
VILLAGE_PATTERNS = [
    ("SUN VILLAGE", re.compile(r"(SUN\s*VILLAGE|サン\s*ヴィレッジ|サンビレッジ)", re.IGNORECASE)),
    ("SEA VILLAGE", re.compile(r"(SEA\s*VILLAGE|シー\s*ヴィレッジ|シービレッジ)", re.IGNORECASE)),
    ("PARK VILLAGE", re.compile(r"(PARK\s*VILLAGE|パーク\s*ヴィレッジ|パークビレッジ)", re.IGNORECASE)),
    ("SKY DUO", re.compile(r"(SKY\s*DUO|スカイ\s*デュオ|スカイデュオ)", re.IGNORECASE)),
    ("PORT VILLAGE", re.compile(r"(PORT\s*VILLAGE|ポート\s*ヴィレッジ|ポートビレッジ)", re.IGNORECASE)),
]
PROPERTY_HINT_RE = re.compile(
    r"(?P<name>[^\n。]{0,30}(?:タワー|レジデンス|マンション|シティ|パーク|ベイ|晴海フラッグ|HARUMI FLAG)[^\n。]{0,30})",
    re.IGNORECASE,
)
BUILDING_LINE_RE = re.compile(
    r"(?P<name>(?:HARUMI FLAG|晴海フラッグ|[A-Za-z0-9一-龥ァ-ヶー・ ]+)"
    r"(?:T棟|A棟|B棟|C棟|D棟|E棟|F棟|[0-9]+階|タワー|レジデンス|マンション|シティ|パーク|ベイ)[^\n]*)",
    re.IGNORECASE,
)


def extract_observations(message: GmailMessage) -> list[PriceObservation]:
    text = "\n".join(part for part in [message.subject, message.body_text] if part)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    observations: list[PriceObservation] = []

    for index, line in enumerate(lines):
        if PRICE_CHANGE_RE.search(line):
            continue
        for match in PRICE_RE.finditer(line):
            price_jpy = parse_price_to_jpy(match.group("price"))
            if price_jpy < 10_000_000:
                continue
            context = build_context(lines, index)
            observation = build_observation(message, context, line, index, price_jpy)
            observations.append(observation)

    return dedupe_observations(observations)


def extract_email_lines(message: GmailMessage) -> list[EmailLine]:
    text = "\n".join(part for part in [message.subject, message.body_text] if part)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email_lines: list[EmailLine] = []
    for index, line in enumerate(lines):
        normalized = normalize_text(line)
        line_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        line_id = stable_line_id(message.message_id, index, line_hash)
        email_lines.append(
            EmailLine(
                line_id=line_id,
                message_id=message.message_id,
                line_index=index,
                line_text=normalized,
                line_hash=line_hash,
            )
        )
    return email_lines


def parse_price_to_jpy(value: str) -> int:
    normalized = value.replace(",", "")
    return int(normalized) * 10_000


def build_context(lines: list[str], index: int) -> str:
    start = max(index - 2, 0)
    end = min(index + 3, len(lines))
    return normalize_text("\n".join(lines[start:end]))


def build_observation(
    message: GmailMessage,
    context: str,
    raw_line: str,
    row_index: int,
    price_jpy: int,
) -> PriceObservation:
    parsed = parse_listing_context(context, price_jpy)
    property_name = parsed.get("property_name")
    building_name = parsed.get("building_name")
    project_name = parsed.get("project_name")
    village_name = parsed.get("village_name")
    building_code = parsed.get("building_code")
    area = parsed.get("area")
    room_type = parsed.get("room_type")
    floor = parsed.get("floor")
    size_sqm = parsed.get("size_sqm")
    previous_price_jpy = parsed.get("previous_price_jpy")
    price_change_jpy = parsed.get("price_change_jpy")
    unit_price_per_tsubo_man = parsed.get("unit_price_per_tsubo_man")
    unit_price_per_tsubo_jpy = parsed.get("unit_price_per_tsubo_jpy")
    direction = parsed.get("direction")
    confidence = score_confidence(
        property_name,
        project_name,
        village_name,
        area,
        room_type,
        size_sqm,
        unit_price_per_tsubo_man,
        direction,
    )
    observation_id = stable_observation_id(message.message_id, context, raw_line, price_jpy)
    return PriceObservation(
        observation_id=observation_id,
        message_id=message.message_id,
        observed_at=message.received_at,
        source_type="price_line",
        row_index=row_index,
        property_name=property_name,
        building_name=building_name,
        project_name=project_name,
        village_name=village_name,
        building_code=building_code,
        area=area,
        room_type=room_type.upper() if room_type else None,
        floor=floor,
        size_sqm=size_sqm,
        price_jpy=price_jpy,
        previous_price_jpy=previous_price_jpy,
        price_change_jpy=price_change_jpy,
        unit_price_per_tsubo_man=unit_price_per_tsubo_man,
        unit_price_per_tsubo_jpy=unit_price_per_tsubo_jpy,
        direction=direction,
        raw_line=normalize_text(raw_line),
        source_text=context,
        parsed_fields_json=json.dumps(parsed, ensure_ascii=False, sort_keys=True),
        confidence=confidence,
    )


def parse_listing_context(context: str, price_jpy: int) -> dict[str, object]:
    lines = [line.strip() for line in context.splitlines() if line.strip()]
    price_values = [parse_price_to_jpy(match.group("price")) for match in PRICE_RE.finditer(context)]
    price_change_jpy = parse_price_change(context)
    previous_price_jpy = infer_previous_price(price_values, price_jpy, price_change_jpy)
    unit_price_per_tsubo_man = extract_unit_price_man(lines, price_values)
    building_name = clean_property_name(find_first(BUILDING_LINE_RE, context, "name"))
    property_name = clean_property_name(find_first(PROPERTY_HINT_RE, context, "name")) or building_name
    project_name = extract_project_name(context)
    village_name = extract_village_name(context)
    building_code = extract_building_code(context)
    area = find_first(AREA_RE, context, 1)
    room_type = find_first(ROOM_RE, context, "room")
    floor = parse_int(find_first(FLOOR_RE, context, "floor"))
    size_sqm = extract_size_sqm(lines, context)
    direction = extract_direction(lines, context)
    return {
        "property_name": property_name,
        "building_name": building_name,
        "project_name": project_name,
        "village_name": village_name,
        "building_code": building_code,
        "area": area,
        "room_type": room_type.upper() if room_type else None,
        "floor": floor,
        "size_sqm": size_sqm,
        "price_jpy": price_jpy,
        "all_price_jpy": price_values,
        "previous_price_jpy": previous_price_jpy,
        "price_change_jpy": price_change_jpy,
        "unit_price_per_tsubo_man": unit_price_per_tsubo_man,
        "unit_price_per_tsubo_jpy": int(round(unit_price_per_tsubo_man * 10_000)) if unit_price_per_tsubo_man else None,
        "direction": direction,
        "raw_context_lines": lines,
        "parser_version": 2,
    }


def extract_size_sqm(lines: list[str], context: str) -> float | None:
    explicit = parse_float(find_first(SIZE_RE, context, "size"))
    if explicit:
        return explicit
    for line in lines:
        if re.fullmatch(r"\d{2,3}(?:\.\d+)?", line):
            return float(line)
    return None


def extract_unit_price_man(lines: list[str], price_values: list[int]) -> float | None:
    price_man_values = {value / 10_000 for value in price_values}
    for line in lines:
        match = TSUBO_RE.search(line)
        if match:
            value = float(match.group("unit"))
            if ("坪" in line or value not in price_man_values) and 200 <= value <= 5000:
                return value
        stripped = line.replace("万円", "").replace("万", "").strip()
        if "," in stripped:
            continue
        if not re.fullmatch(r"\d{2,4}(?:\.\d+)?", stripped):
            continue
        value = float(stripped)
        if value in price_man_values:
            continue
        if 200 <= value <= 5000:
            return value
    return None


def extract_project_name(context: str) -> str | None:
    if HARUMI_FLAG_RE.search(context):
        return "HARUMI FLAG"
    return None


def extract_village_name(context: str) -> str | None:
    for village_name, pattern in VILLAGE_PATTERNS:
        if pattern.search(context):
            return village_name
    return None


def extract_building_code(context: str) -> str | None:
    normalized = context.translate(FULLWIDTH_ASCII_TRANS).upper()
    match = BUILDING_CODE_RE.search(normalized)
    if not match:
        return None
    return f"{match.group('code')}棟"


def clean_property_name(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"^(詳しく見る|物件名|マンション名)\s*", "", value)
    value = re.split(r"\s*(?:販売価格|価格|[0-9]{1,3}(?:,\d{3})*万円|[0-9]{2,3}(?:\.\d+)?平米)", value)[0]
    return normalize_text(value) or None


def extract_direction(lines: list[str], context: str) -> str | None:
    for line in lines:
        match = re.fullmatch(r"(北西|北東|南西|南東|北|南|東|西)(?:向き)?", line)
        if match:
            return match.group(1)
    return find_first(DIRECTION_RE, context, 1)


def parse_price_change(context: str) -> int | None:
    match = PRICE_CHANGE_RE.search(context)
    if not match:
        return None
    amount = parse_price_to_jpy(match.group("amount"))
    return -amount if match.group("sign") in {"▼", "▽", "-"} else amount


def infer_previous_price(
    price_values: list[int],
    price_jpy: int,
    price_change_jpy: int | None,
) -> int | None:
    if not price_change_jpy:
        return None
    candidates = [value for value in price_values if value != price_jpy]
    if candidates:
        return candidates[0]
    return price_jpy - price_change_jpy


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
    project_name: str | None,
    village_name: str | None,
    area: str | None,
    room_type: str | None,
    size_sqm: float | None,
    unit_price: float | None,
    direction: str | None,
) -> float:
    score = 0.35
    score += 0.2 if property_name else 0
    score += 0.1 if project_name else 0
    score += 0.05 if village_name else 0
    score += 0.15 if area else 0
    score += 0.1 if room_type else 0
    score += 0.1 if size_sqm else 0
    score += 0.1 if unit_price else 0
    score += 0.05 if direction else 0
    return min(score, 1.0)


def stable_observation_id(message_id: str, context: str, raw_line: str, price_jpy: int) -> str:
    digest = hashlib.sha256(f"{message_id}|{price_jpy}|{raw_line}|{context}".encode("utf-8")).hexdigest()
    return digest[:32]


def stable_line_id(message_id: str, line_index: int, line_hash: str) -> str:
    digest = hashlib.sha256(f"{message_id}|{line_index}|{line_hash}".encode("utf-8")).hexdigest()
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


def save_email_lines(conn: sqlite3.Connection, email_lines: Iterable[EmailLine]) -> int:
    count = 0
    for line in email_lines:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO email_lines (
                line_id, message_id, line_index, line_text, line_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                line.line_id,
                line.message_id,
                line.line_index,
                line.line_text,
                line.line_hash,
            ),
        )
        count += cursor.rowcount
    return count


def save_observations(conn: sqlite3.Connection, observations: Iterable[PriceObservation]) -> int:
    count = 0
    for observation in observations:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO price_observations (
                observation_id,
                message_id,
                observed_at,
                source_type,
                row_index,
                property_name,
                building_name,
                project_name,
                village_name,
                building_code,
                area,
                room_type,
                floor,
                size_sqm,
                price_jpy,
                previous_price_jpy,
                price_change_jpy,
                unit_price_per_tsubo,
                unit_price_per_tsubo_man,
                unit_price_per_tsubo_jpy,
                direction,
                raw_line,
                source_text,
                parsed_fields_json,
                confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation.observation_id,
                observation.message_id,
                observation.observed_at,
                observation.source_type,
                observation.row_index,
                observation.property_name,
                observation.building_name,
                observation.project_name,
                observation.village_name,
                observation.building_code,
                observation.area,
                observation.room_type,
                observation.floor,
                observation.size_sqm,
                observation.price_jpy,
                observation.previous_price_jpy,
                observation.price_change_jpy,
                int(round(observation.unit_price_per_tsubo_man)) if observation.unit_price_per_tsubo_man else None,
                observation.unit_price_per_tsubo_man,
                observation.unit_price_per_tsubo_jpy,
                observation.direction,
                observation.raw_line,
                observation.source_text,
                observation.parsed_fields_json,
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
    imported_lines = 0
    imported_observations = 0
    for ref in message_refs:
        message = fetch_message(service, ref["id"])
        email_lines = extract_email_lines(message)
        observations = extract_observations(message)
        print(
            f"{message.received_at} | {message.subject[:80]} | "
            f"{len(email_lines)} lines | "
            f"{len(observations)} price observations"
        )
        if conn:
            save_message(conn, message)
            imported_messages += 1
            imported_lines += save_email_lines(conn, email_lines)
            imported_observations += save_observations(conn, observations)

    if conn:
        conn.commit()
        conn.close()

    print(
        f"Done. Imported messages: {imported_messages}. "
        f"New email lines: {imported_lines}. "
        f"New price observations: {imported_observations}."
    )


if __name__ == "__main__":
    main()
