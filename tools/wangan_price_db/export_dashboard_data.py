#!/usr/bin/env python3
"""Export wangan price observations for the static dashboard.

The dashboard should be useful to buyers, so this exporter prefers the
structured tables in the Wangan price newsletter over per-price regex hits.
It emits listing, reduction, and contract rows with comparable dimensions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

TSUBO_SQM = 3.305785
DEFAULT_DB_PATH = "data/wangan_prices.sqlite"
DEFAULT_OUTPUT_PATH = "docs/wangan-price-dashboard/data.js"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to wangan_prices.sqlite.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="Dashboard data.js output path.")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum parser confidence.")
    parser.add_argument(
        "--public-safe",
        action="store_true",
        help="Redact source excerpts that may contain email-derived text.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Project name to include. Repeatable. Defaults to all projects.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = fetch_newsletter_rows(conn)
    if not rows:
        rows = fetch_observation_rows(conn, args.min_confidence, args.project)
    conn.close()

    payload = build_payload(rows, db_path, args.project, args.min_confidence, args.public_safe)
    write_data_js(Path(args.output), payload)
    print(f"Exported {len(payload['observations'])} observations to {args.output}")


def fetch_newsletter_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if "gmail_messages" not in table_names(conn):
        return []

    messages = conn.execute(
        """
        SELECT message_id, received_at, subject, body_text
        FROM gmail_messages
        WHERE subject LIKE '%湾岸マンション価格ナビ%'
        ORDER BY received_at
        """
    ).fetchall()

    rows: list[dict[str, Any]] = []
    for message in messages:
        rows.extend(parse_newsletter_message(dict(message)))
    return rows


def parse_newsletter_message(message: dict[str, Any]) -> list[dict[str, Any]]:
    lines = [line.strip() for line in (message.get("body_text") or "").splitlines() if line.strip()]
    sections = find_sections(lines)
    rows: list[dict[str, Any]] = []

    if "listing" in sections:
        start, end = sections["listing"]
        rows.extend(parse_listing_section(lines, start, end, message))
    if "reduction" in sections:
        start, end = sections["reduction"]
        rows.extend(parse_reduction_section(lines, start, end, message))
    if "contract" in sections:
        start, end = sections["contract"]
        rows.extend(parse_contract_section(lines, start, end, message))
    return rows


def find_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    markers = [
        ("listing", "新着売却物件情報"),
        ("reduction", "値下物件情報"),
        ("contract", "成約事例"),
    ]
    found: list[tuple[str, int]] = []
    for name, marker in markers:
        for index, line in enumerate(lines):
            if line.startswith(marker):
                found.append((name, index))
                break
    found.sort(key=lambda item: item[1])

    sections: dict[str, tuple[int, int]] = {}
    for index, (name, start) in enumerate(found):
        end = found[index + 1][1] if index + 1 < len(found) else len(lines)
        sections[name] = (start, end)
    return sections


KNOWN_AREAS = {
    "豊洲",
    "東雲",
    "有明",
    "晴海",
    "勝どき",
    "月島",
    "佃",
    "台場",
    "芝浦",
    "港南",
    "亀戸",
    "築地",
    "八丁堀",
    "湊",
}


def parse_listing_section(
    lines: list[str],
    start: int,
    end: int,
    message: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = first_area_index(lines, start, end)
    while index + 7 < end:
        chunk = lines[index : index + 8]
        if not looks_like_listing_record(chunk):
            index += 1
            continue
        area, property_name, floor, size_sqm, room_type, price, unit_price, direction = chunk
        price_jpy = parse_man_yen(price)
        size = parse_float(size_sqm)
        rows.append(
            normalize_table_row(
                message=message,
                price_type="listing",
                area=area,
                property_name=property_name,
                floor=parse_floor(floor),
                size_sqm=size,
                room_type=room_type,
                price_jpy=price_jpy,
                previous_price_jpy=None,
                price_change_jpy=None,
                unit_price_per_tsubo_man=parse_unit_price(unit_price) or infer_unit_price(price_jpy, size),
                direction=direction,
                source_line=" / ".join(chunk),
                source_index=index,
            )
        )
        index += 8
    return rows


def parse_reduction_section(
    lines: list[str],
    start: int,
    end: int,
    message: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = first_area_index(lines, start, end)
    while index + 8 < end:
        chunk = lines[index : index + 9]
        if not looks_like_reduction_record(chunk):
            index += 1
            continue
        area, property_name, floor, size_sqm, room_type, previous_price, price, change, direction = chunk
        previous_price_jpy = parse_man_yen(previous_price)
        price_jpy = parse_man_yen(price)
        size = parse_float(size_sqm)
        price_change_jpy = price_jpy - previous_price_jpy if previous_price_jpy and price_jpy else parse_price_change(change)
        rows.append(
            normalize_table_row(
                message=message,
                price_type="reduction",
                area=area,
                property_name=property_name,
                floor=parse_floor(floor),
                size_sqm=size,
                room_type=room_type,
                price_jpy=price_jpy,
                previous_price_jpy=previous_price_jpy,
                price_change_jpy=price_change_jpy,
                unit_price_per_tsubo_man=infer_unit_price(price_jpy, size),
                direction=direction,
                source_line=" / ".join(chunk),
                source_index=index,
            )
        )
        index += 9
    return rows


def parse_contract_section(
    lines: list[str],
    start: int,
    end: int,
    message: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = first_area_index(lines, start, end)
    while index + 7 < end:
        chunk = lines[index : index + 8]
        if not looks_like_listing_record(chunk):
            index += 1
            continue
        area, property_name, floor, size_band, room_type, price, unit_price, direction = chunk
        price_jpy = parse_man_yen(price)
        size = parse_float(size_band)
        rows.append(
            normalize_table_row(
                message=message,
                price_type="contract",
                area=area,
                property_name=property_name,
                floor=parse_floor(floor),
                size_sqm=size,
                room_type=room_type,
                price_jpy=price_jpy,
                previous_price_jpy=None,
                price_change_jpy=None,
                unit_price_per_tsubo_man=parse_unit_price(unit_price) or infer_unit_price(price_jpy, size),
                direction=direction,
                source_line=" / ".join(chunk),
                source_index=index,
            )
        )
        index += 8
    return rows


def normalize_table_row(
    *,
    message: dict[str, Any],
    price_type: str,
    area: str,
    property_name: str,
    floor: int | None,
    size_sqm: float | None,
    room_type: str | None,
    price_jpy: int | None,
    previous_price_jpy: int | None,
    price_change_jpy: int | None,
    unit_price_per_tsubo_man: float | None,
    direction: str | None,
    source_line: str,
    source_index: int,
) -> dict[str, Any]:
    change_rate = price_change_jpy / previous_price_jpy if price_change_jpy and previous_price_jpy else None
    return {
        "id": f"{message.get('message_id')}:{price_type}:{source_index}",
        "observedAt": message.get("received_at"),
        "sourceType": "newsletter_table",
        "priceType": price_type,
        "projectName": clean_text(property_name),
        "propertyName": clean_text(property_name),
        "buildingName": None,
        "villageName": infer_village_name(property_name),
        "buildingCode": infer_building_code(property_name),
        "area": clean_text(area),
        "roomType": clean_text(room_type),
        "floor": floor,
        "sizeSqm": size_sqm,
        "sizeBand": size_band(size_sqm),
        "priceJpy": price_jpy,
        "priceBand": price_band(price_jpy),
        "previousPriceJpy": previous_price_jpy,
        "priceChangeJpy": price_change_jpy,
        "priceChangeRate": change_rate,
        "unitPricePerTsuboMan": unit_price_per_tsubo_man,
        "unitPriceBand": unit_price_band(unit_price_per_tsubo_man),
        "direction": clean_text(direction),
        "confidence": 1.0,
        "rawLine": source_line,
        "sourceExcerpt": source_line,
        "observedMonth": month_key(message.get("received_at")),
        "areaMedianUnit": None,
        "discountToAreaMedianPct": None,
        "bargainScore": None,
    }


def first_area_index(lines: list[str], start: int, end: int) -> int:
    for index in range(start, end):
        if lines[index] in KNOWN_AREAS:
            return index
    return end


def looks_like_listing_record(chunk: list[str]) -> bool:
    return (
        len(chunk) == 8
        and chunk[0] in KNOWN_AREAS
        and parse_floor(chunk[2]) is not None
        and parse_float(chunk[3]) is not None
        and parse_man_yen(chunk[5]) is not None
    )


def looks_like_reduction_record(chunk: list[str]) -> bool:
    return (
        len(chunk) == 9
        and chunk[0] in KNOWN_AREAS
        and parse_floor(chunk[2]) is not None
        and parse_float(chunk[3]) is not None
        and parse_man_yen(chunk[5]) is not None
        and parse_man_yen(chunk[6]) is not None
    )


def fetch_observation_rows(conn: sqlite3.Connection, min_confidence: float, projects: list[str]) -> list[dict[str, Any]]:
    columns = table_columns(conn, "price_observations")
    select_columns = [
        "observation_id",
        "observed_at",
        optional_column(columns, "source_type"),
        "property_name",
        optional_column(columns, "building_name"),
        optional_column(columns, "project_name"),
        optional_column(columns, "village_name"),
        optional_column(columns, "building_code"),
        "area",
        "room_type",
        "floor",
        "size_sqm",
        "price_jpy",
        optional_column(columns, "previous_price_jpy"),
        optional_column(columns, "price_change_jpy"),
        optional_column(columns, "unit_price_per_tsubo_man"),
        "direction",
        "confidence",
        optional_column(columns, "raw_line"),
        "source_text",
    ]
    params: list[Any] = [min_confidence]
    where_clauses = ["confidence >= ?"]
    if projects:
        placeholders = ", ".join("?" for _ in projects)
        where_clauses.append(f"COALESCE(project_name, property_name, building_name, area, 'Unknown') IN ({placeholders})")
        params.extend(projects)

    sql = f"""
        SELECT {", ".join(select_columns)}
        FROM price_observations
        WHERE {" AND ".join(where_clauses)}
        ORDER BY observed_at DESC, price_jpy DESC
    """
    return [normalize_observation_row(dict(row)) for row in conn.execute(sql, params)]


def table_names(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}


def optional_column(columns: set[str], column_name: str) -> str:
    if column_name in columns:
        return column_name
    return f"NULL AS {column_name}"


def build_payload(
    rows: list[dict[str, Any]],
    db_path: Path,
    selected_projects: list[str],
    min_confidence: float,
    public_safe: bool,
) -> dict[str, Any]:
    observations = enrich_rows(rows)
    if selected_projects:
        selected = set(selected_projects)
        observations = [row for row in observations if row.get("projectName") in selected]
    if public_safe:
        observations = [redact_for_public(row) for row in observations]
    projects = sorted({row["projectName"] for row in observations if row["projectName"]})
    areas = sorted({row["area"] for row in observations if row["area"]})
    price_types = sorted({row["priceType"] for row in observations if row["priceType"]})
    size_bands = sorted({row["sizeBand"] for row in observations if row["sizeBand"]}, key=size_band_sort_key)
    months = sorted({row["observedMonth"] for row in observations if row["observedMonth"]})

    return {
        "schemaVersion": 2,
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {
            "dbPath": str(db_path),
            "selectedProjects": selected_projects,
            "minConfidence": min_confidence,
            "priceType": "mixed",
            "publicSafe": public_safe,
        },
        "projects": projects,
        "areas": areas,
        "priceTypes": price_types,
        "sizeBands": size_bands,
        "months": months,
        "summary": build_summary(observations),
        "observations": observations,
    }


def redact_for_public(row: dict[str, Any]) -> dict[str, Any]:
    copy = dict(row)
    copy["rawLine"] = None
    copy["sourceExcerpt"] = None
    return copy


def normalize_observation_row(row: dict[str, Any]) -> dict[str, Any]:
    project_name = clean_text(row.get("project_name")) or infer_project_name(row)
    village_name = clean_text(row.get("village_name"))
    building_code = clean_text(row.get("building_code"))
    size_sqm = as_float(row.get("size_sqm"))
    price_jpy = as_int(row.get("price_jpy"))
    unit_price = as_float(row.get("unit_price_per_tsubo_man")) or infer_unit_price(price_jpy, size_sqm)
    previous_price_jpy = as_int(row.get("previous_price_jpy"))
    price_change_jpy = as_int(row.get("price_change_jpy"))

    return {
        "id": row.get("observation_id"),
        "observedAt": row.get("observed_at"),
        "sourceType": clean_text(row.get("source_type")),
        "priceType": infer_price_type(previous_price_jpy, price_change_jpy),
        "projectName": project_name,
        "propertyName": clean_text(row.get("property_name")),
        "buildingName": clean_text(row.get("building_name")),
        "villageName": village_name,
        "buildingCode": building_code,
        "area": clean_text(row.get("area")),
        "roomType": clean_text(row.get("room_type")),
        "floor": as_int(row.get("floor")),
        "sizeSqm": size_sqm,
        "sizeBand": size_band(size_sqm),
        "priceJpy": price_jpy,
        "priceBand": price_band(price_jpy),
        "previousPriceJpy": previous_price_jpy,
        "priceChangeJpy": price_change_jpy,
        "priceChangeRate": price_change_jpy / previous_price_jpy if price_change_jpy and previous_price_jpy else None,
        "unitPricePerTsuboMan": unit_price,
        "unitPriceBand": unit_price_band(unit_price),
        "direction": clean_text(row.get("direction")),
        "confidence": as_float(row.get("confidence")),
        "rawLine": clean_text(row.get("raw_line")),
        "sourceExcerpt": excerpt(row.get("source_text")),
        "observedMonth": month_key(row.get("observed_at")),
        "areaMedianUnit": None,
        "discountToAreaMedianPct": None,
        "bargainScore": None,
    }


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    area_medians = {
        area: median([row["unitPricePerTsuboMan"] for row in area_rows if row.get("unitPricePerTsuboMan")])
        for area, area_rows in group_by(rows, "area").items()
    }
    enriched: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        area_median = area_medians.get(copy.get("area"))
        unit_price = as_float(copy.get("unitPricePerTsuboMan"))
        discount = (area_median - unit_price) / area_median if area_median and unit_price else None
        copy["areaMedianUnit"] = area_median
        copy["discountToAreaMedianPct"] = discount
        copy["bargainScore"] = bargain_score(copy, discount)
        enriched.append(copy)
    return enriched


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [row["priceJpy"] for row in rows if row.get("priceJpy")]
    units = [row["unitPricePerTsuboMan"] for row in rows if row.get("unitPricePerTsuboMan")]
    reductions = [row for row in rows if (row.get("priceChangeJpy") or 0) < 0]
    return {
        "observationCount": len(rows),
        "priceMedianJpy": median(prices),
        "unitMedianMan": median(units),
        "reductionCount": len(reductions),
        "reductionShare": len(reductions) / len(rows) if rows else None,
        "latestObservedAt": max((row["observedAt"] for row in rows if row.get("observedAt")), default=None),
        "earliestObservedAt": min((row["observedAt"] for row in rows if row.get("observedAt")), default=None),
    }


def infer_project_name(row: dict[str, Any]) -> str:
    for column in ("property_name", "building_name", "source_text", "area"):
        value = clean_text(row.get(column))
        if value:
            return value
    return "Unknown"


def infer_village_name(property_name: str | None) -> str | None:
    text = clean_text(property_name)
    if not text:
        return None
    patterns = [
        "HARUMI FLAG",
        "晴海フラッグ",
        "シティタワーズ東京ベイ",
        "シティタワーズ豊洲",
        "パークタワー晴海",
        "ザ・パークハウス 晴海タワーズ",
        "Wコンフォートタワーズ",
        "Ｗコンフォートタワーズ",
        "ブリリア有明",
        "Brillia 有明",
    ]
    for pattern in patterns:
        if pattern in text:
            return pattern
    return text


def infer_building_code(property_name: str | None) -> str | None:
    text = clean_text(property_name)
    if not text:
        return None
    match = re.search(r"([A-ZＡ-Ｚ]棟|タワー[ABCＡＢＣ]?|TOWER[&A-Z ]*)", text, re.IGNORECASE)
    return match.group(1) if match else None


def infer_price_type(previous_price_jpy: int | None, price_change_jpy: int | None) -> str:
    if previous_price_jpy or price_change_jpy:
        return "reduction" if (price_change_jpy or 0) < 0 else "revision"
    return "listing"


def infer_unit_price(price_jpy: int | None, size_sqm: float | None) -> float | None:
    if not price_jpy or not size_sqm:
        return None
    return price_jpy / 10_000 / (size_sqm / TSUBO_SQM)


def parse_man_yen(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"(\d{1,3}(?:,\d{3})+|\d{2,6})", text)
    if not match:
        return None
    return int(match.group(1).replace(",", "")) * 10_000


def parse_price_change(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    amount = parse_man_yen(text)
    if amount is None:
        return None
    return -amount if any(sign in text for sign in ("▼", "▽", "-")) else amount


def parse_unit_price(value: Any) -> float | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"(\d{2,4}(?:\.\d+)?)", text.replace(",", ""))
    return float(match.group(1)) if match else None


def parse_floor(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_float(value: Any) -> float | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    return float(match.group(0)) if match else None


def size_band(value: float | None) -> str | None:
    if value is None:
        return None
    lower = int(value // 10) * 10
    if lower >= 100:
        return "100㎡以上"
    return f"{lower}㎡台"


def price_band(value: int | None) -> str | None:
    if value is None:
        return None
    oku = value / 100_000_000
    lower = int(oku // 0.5) * 0.5
    upper = lower + 0.5
    if lower >= 5:
        return "5億円以上"
    return f"{lower:.1f}-{upper:.1f}億円"


def unit_price_band(value: float | None) -> str | None:
    if value is None:
        return None
    lower = int(value // 100) * 100
    if lower >= 1500:
        return "1500万/坪以上"
    return f"{lower}-{lower + 99}万/坪"


def month_key(value: Any) -> str | None:
    text = clean_text(value)
    return text[:7] if text else None


def bargain_score(row: dict[str, Any], discount_to_area_median: float | None) -> float | None:
    if row.get("priceType") not in {"reduction", "listing"}:
        return None
    score = 0.0
    if discount_to_area_median:
        score += max(0.0, discount_to_area_median) * 100
    change = as_int(row.get("priceChangeJpy"))
    if change and change < 0:
        score += min(abs(change) / 1_000_000, 20)
    floor = as_int(row.get("floor"))
    size_sqm = as_float(row.get("sizeSqm"))
    if floor and floor >= 20:
        score += 5
    if size_sqm and size_sqm >= 70:
        score += 3
    if floor and floor <= 5:
        score -= 4
    return round(score, 2)


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        label = row.get(key)
        if not label:
            continue
        groups.setdefault(label, []).append(row)
    return groups


def median(values: list[Any]) -> float | int | None:
    numbers = sorted(value for value in (as_float(value) for value in values) if value is not None)
    if not numbers:
        return None
    middle = len(numbers) // 2
    if len(numbers) % 2:
        return numbers[middle]
    return (numbers[middle - 1] + numbers[middle]) / 2


def size_band_sort_key(value: str) -> int:
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else 9999


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def excerpt(value: Any, limit: int = 220) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def write_data_js(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    output_path.write_text(f"window.WANGAN_PRICE_DASHBOARD_DATA = {encoded};\n", encoding="utf-8")


if __name__ == "__main__":
    main()
