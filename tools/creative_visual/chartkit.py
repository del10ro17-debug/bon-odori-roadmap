#!/usr/bin/env python3
"""Reusable charting helpers for the HQ creative-visual skill.

データ可視化は画像生成AIではなくコードで正確に描く、という方針のための共通基盤。
matplotlib をHQの統一スタイル（日本語フォント・配色・余白）で初期化し、
保存まで一括で行うヘルパーを提供する。
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

# HQ ブランド配色（落ち着いたネイビー基調 + アクセント）。
HQ_COLORS = [
    "#1f3a5f",
    "#3d7ea6",
    "#e07a5f",
    "#81b29a",
    "#f2cc8f",
    "#9a8c98",
    "#5c4d7d",
]


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
            "axes.edgecolor": "#cccccc",
            "axes.grid": True,
            "grid.color": "#e6e6e6",
            "grid.linewidth": 0.8,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.prop_cycle": plt.cycler(color=HQ_COLORS),
            "figure.dpi": 130,
            "savefig.bbox": "tight",
        }
    )


def new_figure(width: float = 9.0, height: float = 5.0) -> tuple[Figure, plt.Axes]:
    apply_hq_style()
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def annotate_bars(ax: plt.Axes, fmt: str = "{:.0f}", offset: float = 3.0) -> None:
    for container in ax.containers:
        ax.bar_label(container, fmt=lambda v: fmt.format(v), padding=offset, fontsize=9)


def save(fig: Figure, output: str | Path) -> Path:
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
) -> Path:
    fig, ax = new_figure(height=max(4.0, 0.5 * len(labels) + 1.5))
    bars = ax.barh(list(labels), list(values), color=HQ_COLORS[0])
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.bar_label(bars, fmt=lambda v: value_fmt.format(v), padding=4, fontsize=9)
    return save(fig, output)


def line_trend(
    x: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
) -> Path:
    fig, ax = new_figure()
    for name, values in series.items():
        ax.plot(list(x), list(values), marker="o", linewidth=2.2, label=name)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if len(series) > 1:
        ax.legend(frameon=False)
    return save(fig, output)


def grouped_bar(
    categories: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
    value_fmt: str | None = "{:,.0f}",
) -> Path:
    import numpy as np

    fig, ax = new_figure(width=max(7.0, 1.6 * len(categories)))
    n = len(series)
    x = np.arange(len(categories))
    width = 0.8 / max(n, 1)
    for i, (name, values) in enumerate(series.items()):
        offset = (i - (n - 1) / 2) * width
        bars = ax.bar(x + offset, list(values), width, label=name, color=HQ_COLORS[i % len(HQ_COLORS)])
        if value_fmt:
            ax.bar_label(bars, fmt=lambda v: value_fmt.format(v), padding=3, fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(list(categories))
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    return save(fig, output)


def stacked_bar(
    categories: Sequence[str],
    series: dict[str, Sequence[float]],
    *,
    title: str,
    ylabel: str,
    output: str | Path,
    value_fmt: str | None = "{:,.0f}",
) -> Path:
    import numpy as np

    fig, ax = new_figure(width=max(7.0, 1.6 * len(categories)))
    bottom = np.zeros(len(categories))
    for i, (name, values) in enumerate(series.items()):
        vals = np.array(values, dtype=float)
        bars = ax.bar(list(categories), vals, bottom=bottom, label=name, color=HQ_COLORS[i % len(HQ_COLORS)])
        if value_fmt:
            ax.bar_label(bars, labels=[value_fmt.format(v) for v in vals], label_type="center", fontsize=8, color="white")
        bottom += vals
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    return save(fig, output)
