#!/usr/bin/env python3
"""Reusable charting helpers for the HQ creative-visual skill.

データ可視化は画像生成AIではなくコードで正確に描く、という方針のための共通基盤。
配色・設計原則は デジタル庁「ダッシュボードデザイン実践ガイドブック」(2026) に準拠する:
- グラフの原点は原則0 / 軸を歪めない
- 色数を絞る（1〜5色）/ 色のみで識別しない（数値を併記）
- 不要な装飾（3D・影・過剰なグリッド）を使わない
- タイトルにデータ種別（月次推移・累計など）を明記
- メタ情報（出典・時点）を併記
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# macOS 標準。Linux/CI では Noto Sans CJK JP などに差し替える。
JP_FONT_CANDIDATES = [
    "Hiragino Sans",
    "Hiragino Maru Gothic Pro",
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "IPAexGothic",
    "Yu Gothic",
]

# デジタル庁 デザインシステムのカラーパレット（チャート向けに 600/900 系を抜粋）。
# 色覚多様性に配慮し、隣接系列が見分けやすい順に並べる。色数は 1〜5 に絞ること。
DA_PALETTE = [
    "#3460FB",  # Blue 600
    "#FB5B01",  # Orange 600
    "#259D63",  # Green 600
    "#00A3BF",  # Cyan 600
    "#FE3939",  # Red 600
    "#767676",  # Solid Gray 536
    "#008BF2",  # Light Blue 600
]
# 単系列の既定色（白背景に対しコントラスト比 4.5:1 以上）。
PRIMARY = "#0017C1"  # Blue 900
# セマンティックカラー（増減表現）。
POSITIVE = "#197A4B"
NEGATIVE = "#CE0000"

# 後方互換: 旧名 HQ_COLORS を残す。
HQ_COLORS = DA_PALETTE


def pick_jp_font() -> str | None:
    available = {f.name for f in fm.fontManager.ttflist}
    for name in JP_FONT_CANDIDATES:
        if name in available:
            return name
    return None


def apply_hq_style() -> None:
    font = pick_jp_font()
    if font:
        plt.rcParams["font.family"] = font
    plt.rcParams.update(
        {
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#CCCCCC",
            # 不要な要素は削除する: 枠線は下・左のみ、グリッドは薄く片軸だけ
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#ECECEC",
            "grid.linewidth": 0.8,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelcolor": "#333333",
            "text.color": "#333333",
            "xtick.color": "#626264",
            "ytick.color": "#626264",
            "axes.prop_cycle": plt.cycler(color=DA_PALETTE),
            "figure.dpi": 130,
            "savefig.bbox": "tight",
        }
    )


def new_figure(width: float = 9.0, height: float = 5.0) -> tuple[Figure, plt.Axes]:
    apply_hq_style()
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def add_source(fig: Figure, source: str | None) -> None:
    """メタ情報（出典・時点）を図の右下に小さく添える。ガイドブックの「メタ情報を記載する」。"""
    if source:
        fig.text(0.99, 0.005, source, ha="right", va="bottom", fontsize=7.5, color="#767676")


def save(fig: Figure, output: str | Path, *, source: str | None = None) -> Path:
    add_source(fig, source)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def horizontal_bar(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str,
    xlabel: str,
    output: str | Path,
    value_fmt: str = "{:.0f}",
    source: str | None = None,
    color: str = PRIMARY,
) -> Path:
    fig, ax = new_figure(height=max(4.0, 0.5 * len(labels) + 1.5))
    bars = ax.barh(list(labels), list(values), color=color)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    # 数値を併記（色のみに依存しない / アクセシビリティ）
    ax.bar_label(bars, fmt=lambda v: value_fmt.format(v), padding=4, fontsize=9)
    return save(fig, output, source=source)


def line_trend(
    x: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
    source: str | None = None,
    markers: Sequence[str] = ("o", "s", "^", "D", "v"),
) -> Path:
    fig, ax = new_figure()
    # 色のみで識別しない: 系列ごとにマーカー形状も変える
    for i, (name, values) in enumerate(series.items()):
        ax.plot(
            list(x),
            list(values),
            marker=markers[i % len(markers)],
            linewidth=2.2,
            label=name,
            color=DA_PALETTE[i % len(DA_PALETTE)],
        )
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if len(series) > 1:
        ax.legend(frameon=False)
    return save(fig, output, source=source)


def grouped_bar(
    categories: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
    value_fmt: str | None = "{:,.0f}",
    source: str | None = None,
) -> Path:
    import numpy as np

    fig, ax = new_figure(width=max(7.0, 1.6 * len(categories)))
    n = len(series)
    x = np.arange(len(categories))
    width = 0.8 / max(n, 1)
    for i, (name, values) in enumerate(series.items()):
        offset = (i - (n - 1) / 2) * width
        bars = ax.bar(x + offset, list(values), width, label=name, color=DA_PALETTE[i % len(DA_PALETTE)])
        if value_fmt:
            ax.bar_label(bars, fmt=lambda v: value_fmt.format(v), padding=3, fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(list(categories))
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)  # 棒グラフの原点は0
    ax.grid(axis="x", visible=False)
    if n > 1:
        ax.legend(frameon=False)
    return save(fig, output, source=source)


def stacked_bar(
    categories: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
    value_fmt: str | None = "{:,.0f}",
    source: str | None = None,
) -> Path:
    import numpy as np

    fig, ax = new_figure(width=max(7.0, 1.6 * len(categories)))
    bottom = np.zeros(len(categories))
    for i, (name, values) in enumerate(series.items()):
        vals = np.array(values, dtype=float)
        bars = ax.bar(list(categories), vals, bottom=bottom, label=name, color=DA_PALETTE[i % len(DA_PALETTE)])
        if value_fmt:
            ax.bar_label(bars, labels=[value_fmt.format(v) for v in vals], label_type="center", fontsize=8, color="white")
        bottom += vals
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)  # 原点は0
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    return save(fig, output, source=source)
