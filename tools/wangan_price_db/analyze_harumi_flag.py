#!/usr/bin/env python3
"""Analyze HARUMI FLAG listing observations in the wangan price database."""

from __future__ import annotations

import argparse
import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

TSUBO_SQM = 3.305785
DEFAULT_DB_PATH = "data/wangan_prices.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to wangan_prices.sqlite.")
    parser.add_argument("--limit", type=int, default=20, help="Recent observations to show.")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum parser confidence.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = fetch_harumi_rows(conn, args.min_confidence)
    conn.close()

    print_report(rows, args.limit)


def fetch_harumi_rows(conn: sqlite3.Connection, min_confidence: float) -> list[dict[str, Any]]:
    columns = table_columns(conn, "price_observations")
    select_columns = [
        "observed_at",
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
    where_clauses = [
        "COALESCE(property_name, '') LIKE '%HARUMI FLAG%'",
        "COALESCE(property_name, '') LIKE '%晴海フラッグ%'",
        "COALESCE(building_name, '') LIKE '%HARUMI FLAG%'",
        "COALESCE(building_name, '') LIKE '%晴海フラッグ%'",
        "COALESCE(source_text, '') LIKE '%HARUMI FLAG%'",
        "COALESCE(source_text, '') LIKE '%晴海フラッグ%'",
    ]
    if "project_name" in columns:
        where_clauses.append("project_name = 'HARUMI FLAG'")

    sql = f"""
        SELECT {", ".join(select_columns)}
        FROM price_observations
        WHERE confidence >= ?
          AND ({' OR '.join(where_clauses)})
        ORDER BY observed_at DESC, price_jpy DESC
    """
    return [dict(row) for row in conn.execute(sql, (min_confidence,))]


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}


def optional_column(columns: set[str], column_name: str) -> str:
    if column_name in columns:
        return column_name
    return f"NULL AS {column_name}"


def print_report(rows: list[dict[str, Any]], recent_limit: int) -> None:
    print("# HARUMI FLAG Listing Analysis")
    print()
    if not rows:
        print("No HARUMI FLAG observations found.")
        return

    enrich_rows(rows)
    prices = [row["price_jpy"] for row in rows if row.get("price_jpy")]
    unit_prices = [row["unit_price_per_tsubo_man"] for row in rows if row.get("unit_price_per_tsubo_man")]
    price_changes = [row["price_change_jpy"] for row in rows if row.get("price_change_jpy")]

    print("## Summary")
    print(f"- Observations: {len(rows)}")
    print(f"- Price range: {format_jpy(min(prices))} - {format_jpy(max(prices))}")
    print(f"- Median price: {format_jpy(statistics.median(prices))}")
    if unit_prices:
        print(f"- Tsubo unit range: {min(unit_prices):,.1f} - {max(unit_prices):,.1f} man/tsubo")
        print(f"- Median tsubo unit: {statistics.median(unit_prices):,.1f} man/tsubo")
    if price_changes:
        decreases = [value for value in price_changes if value < 0]
        print(f"- Price change observations: {len(price_changes)}")
        if decreases:
            print(f"- Price decreases: {len(decreases)}, median decrease: {format_jpy(abs(statistics.median(decreases)))}")
    print()

    print_group("By Village And Building", rows, lambda row: group_key(row, "village_name", "building_code"))
    print_group("By Size Band", rows, lambda row: size_band(row.get("size_sqm")))
    print_recent(rows, recent_limit)


def enrich_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        if row.get("unit_price_per_tsubo_man"):
            continue
        size_sqm = row.get("size_sqm")
        price_jpy = row.get("price_jpy")
        if size_sqm and price_jpy:
            row["unit_price_per_tsubo_man"] = price_jpy / 10_000 / (size_sqm / TSUBO_SQM)


def print_group(title: str, rows: list[dict[str, Any]], key_func) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key_func(row)].append(row)

    print(f"## {title}")
    print("| Segment | Count | Median Price | Median Tsubo Unit |")
    print("|---|---:|---:|---:|")
    for key, values in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        prices = [row["price_jpy"] for row in values if row.get("price_jpy")]
        unit_prices = [row["unit_price_per_tsubo_man"] for row in values if row.get("unit_price_per_tsubo_man")]
        median_price = format_jpy(statistics.median(prices)) if prices else "-"
        median_unit = f"{statistics.median(unit_prices):,.1f}" if unit_prices else "-"
        print(f"| {key} | {len(values)} | {median_price} | {median_unit} |")
    print()


def group_key(row: dict[str, Any], *columns: str) -> str:
    values = [str(row.get(column)) for column in columns if row.get(column)]
    return " ".join(values) if values else "Unknown"


def size_band(size_sqm: float | None) -> str:
    if not size_sqm:
        return "Unknown"
    lower = int(size_sqm // 10 * 10)
    upper = lower + 10
    return f"{lower}-{upper} sqm"


def print_recent(rows: list[dict[str, Any]], limit: int) -> None:
    print(f"## Recent Observations (Top {limit})")
    print("| Observed At | Village | Building | Floor | Layout | Size | Price | Tsubo Unit | Direction | Confidence |")
    print("|---|---|---|---:|---|---:|---:|---:|---|---:|")
    for row in rows[:limit]:
        print(
            "| "
            f"{row.get('observed_at') or '-'} | "
            f"{row.get('village_name') or '-'} | "
            f"{row.get('building_code') or '-'} | "
            f"{row.get('floor') or '-'} | "
            f"{row.get('room_type') or '-'} | "
            f"{format_number(row.get('size_sqm'))} | "
            f"{format_jpy(row.get('price_jpy'))} | "
            f"{format_number(row.get('unit_price_per_tsubo_man'))} | "
            f"{row.get('direction') or '-'} | "
            f"{format_number(row.get('confidence'))} |"
        )


def format_jpy(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value / 100_000_000:,.2f} oku"


def format_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


if __name__ == "__main__":
    main()
