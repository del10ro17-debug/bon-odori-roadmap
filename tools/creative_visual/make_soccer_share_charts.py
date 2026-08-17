#!/usr/bin/env python3
"""少年サッカー動画の共有手段比較チャート。

数値は公開仕様と保護者コメントに基づく。BANDの無料総容量GBは公式が固定値を
前面に出していないため、総容量棒グラフには入れない。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import chartkit

OUTDIR = Path(__file__).resolve().parents[2] / "docs" / "creative-visual"
SOURCE = (
    "出典: BANDヘルプ（1本3GB・60分以内）/ YouTubeヘルプ / Google One / "
    "XbotGo公式。BAND総容量GBは非公開のため除外。時点 2026-08-17"
)


def _apply_linux_jp_font() -> None:
    extra = ["WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "Droid Sans Fallback"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in extra:
        if name in available:
            plt.rcParams["font.family"] = name
            return


def make_fit_scores(outdir: Path) -> Path:
    """3観点×4サービスの向き（0=弱い, 3=強い）。"""
    _apply_linux_jp_font()
    return chartkit.grouped_bar(
        categories=["無料で長く残せる", "チーム外に漏れにくい", "じいじばあばに見せやすい"],
        series={
            "BAND": [2, 3, 0],
            "YouTube限定公開": [3, 1, 3],
            "Google フォト": [1, 2, 3],
            "XbotGo Cloud": [1, 1, 3],
        },
        title="少年サッカー動画の共有手段の向き（3点満点）",
        ylabel="向き（0=弱い / 3=強い）",
        output=outdir / "soccer-video-share-fit.png",
        value_fmt="{:.0f}",
        source=SOURCE + " / 採点定義は soccer-video-share-comparison.md",
    )


def make_free_gb(outdir: Path) -> Path:
    """無料総容量が公式に出ているサービスのみ。"""
    _apply_linux_jp_font()
    return chartkit.horizontal_bar(
        labels=["Google フォト / Drive / Gmail 合算", "XbotGo Cloud"],
        values=[15, 20],
        title="無料アカウントの総容量（公式値があるサービス）",
        xlabel="無料容量（GB）",
        output=outdir / "soccer-video-share-free-gb.png",
        value_fmt="{:.0f} GB",
        source=(
            "出典: Google One ヘルプ（15GB合算）/ XbotGo Cloud（20GB）。"
            "YouTubeは総容量無制限（1本256GBまたは12時間）。"
            "BANDは1本3GB・60分以内、総容量はBAND設定依存。時点 2026-08-17"
        ),
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fit = make_fit_scores(OUTDIR)
    gb = make_free_gb(OUTDIR)
    print(fit)
    print(gb)


if __name__ == "__main__":
    main()
