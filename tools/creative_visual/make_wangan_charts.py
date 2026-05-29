#!/usr/bin/env python3
"""湾岸価格DBのダッシュボードデータ(data.js)から正確なグラフを生成するデモ兼実用スクリプト。

画像生成AIではなく、実データ + matplotlib で数値の正しいチャートを描く。
出力先は docs/creative-visual/ 配下のPNG。
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import chartkit

DEFAULT_DATA = "docs/wangan-price-dashboard/data.js"
DEFAULT_OUTDIR = "docs/creative-visual"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=DEFAULT_DATA, help="dashboard data.js path")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="output directory for PNGs")
    parser.add_argument("--top", type=int, default=10, help="エリア別グラフの表示件数")
    return parser.parse_args()


def load_observations(data_path: Path) -> list[dict[str, Any]]:
    text = data_path.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}") + 1
    payload = json.loads(text[start:end])
    return payload.get("observations", [])


def median(values: list[float]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    return statistics.median(nums) if nums else None


def area_median_unit_chart(rows: list[dict[str, Any]], outdir: Path, top: int) -> Path:
    by_area: dict[str, list[float]] = {}
    for row in rows:
        area = row.get("area")
        unit = row.get("unitPricePerTsuboMan")
        if area and isinstance(unit, (int, float)):
            by_area.setdefault(area, []).append(unit)

    medians = {area: median(vals) for area, vals in by_area.items()}
    ranked = sorted(
        ((a, m, len(by_area[a])) for a, m in medians.items() if m is not None),
        key=lambda t: t[1],
        reverse=True,
    )[:top]

    labels = [f"{a}（n={n}）" for a, _, n in ranked]
    values = [round(m, 1) for _, m, _ in ranked]
    return chartkit.horizontal_bar(
        labels,
        values,
        title="湾岸エリア別 坪単価（中央値）",
        xlabel="万円 / 坪",
        output=outdir / "wangan_area_unit_price.png",
        value_fmt="{:.0f}",
    )


def monthly_trend_chart(rows: list[dict[str, Any]], outdir: Path) -> Path:
    by_month: dict[str, list[float]] = {}
    for row in rows:
        month = row.get("observedMonth")
        unit = row.get("unitPricePerTsuboMan")
        if month and isinstance(unit, (int, float)):
            by_month.setdefault(month, []).append(unit)

    months = sorted(by_month)
    medians = [round(median(by_month[m]) or 0, 1) for m in months]
    return chartkit.line_trend(
        months,
        {"坪単価 中央値": medians},
        title="湾岸エリア全体 坪単価の月次推移（中央値）",
        ylabel="万円 / 坪",
        output=outdir / "wangan_monthly_trend.png",
    )


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(f"data not found: {data_path}")

    rows = load_observations(data_path)
    outdir = Path(args.outdir)
    outputs = [
        area_median_unit_chart(rows, outdir, args.top),
        monthly_trend_chart(rows, outdir),
    ]
    print(f"observations: {len(rows)}")
    for out in outputs:
        print(f"saved: {out}")


if __name__ == "__main__":
    main()
