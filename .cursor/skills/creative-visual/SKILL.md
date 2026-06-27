---
name: creative-visual
description: >-
  Produces images and data visualizations: charts/graphs from real data
  (matplotlib / Cursor Canvas) and design assets (flyers, icons, SNS images,
  mockups) via image generation. Use when the user mentions グラフ, チャート,
  可視化, 図, 絵, イラスト, ロゴ, チラシ, アイコン, バナー, モックアップ, ダッシュボード画像, or asks to
  visualize numbers / make a picture.
compatibility: "Claude Code required. Python 3, matplotlib must be installed (tools/creative_visual/.venv). Image generation requires GenerateImage tool support."
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# クリエイティブ／可視化

絵（デザイン）とグラフ（データ可視化）を作る部門。**2系統を必ず使い分ける。**

## 鉄則

| 種類 | 作り方 | 使うもの |
|---|---|---|
| **データ可視化**（数字のグラフ） | コードで正確に描く | matplotlib（静止PNG）/ Cursor Canvas（動的） |
| **デザイン**（絵・イラスト・レイアウト） | 画像生成 | GenerateImage ツール |

**絶対禁止**: 売上・価格・KPI などの数値グラフを画像生成AIで作ること（数字が捏造される）。数値は必ずコードで描画する。

## データ可視化の手順

1. データソースを特定（例: `docs/wangan-price-dashboard/data.js`、経費CSV、`registry.yaml`、Notion）
2. 共通基盤 `tools/creative_visual/chartkit.py` を使う（デジタル庁配色・日本語フォント `Hiragino Sans`・原点0・数値併記まで内蔵）
3. 静止画でよければ matplotlib で PNG を `docs/creative-visual/` に出力
4. 操作できる動的グラフが要るときは Cursor Canvas（`.cursor/skills-cursor/canvas/SKILL.md` を Read）

詳細な設計基準・カラーパレット・チェックリストは `references/charting-standards.md` を参照。

### 実行例（湾岸価格DB）

```bash
cd tools/creative_visual
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 初回のみ
.venv/bin/python make_wangan_charts.py \
  --data ../../docs/wangan-price-dashboard/data.js \
  --outdir ../../docs/creative-visual
```

新しいグラフは `chartkit.horizontal_bar` / `line_trend` / `new_figure` を呼んで追加する。

## デザインの手順

1. 用途・サイズ・文字・配色・スタイルを1行で固める（曖昧なら1問だけ確認）
2. GenerateImage で生成（参考画像があれば `reference_image_paths` に渡す）
3. ロゴ・チラシ等の確定物は用途を添えて保存場所を提案

## 他部門との接点

| 連携先 | 例 |
|---|---|
| 湾岸不動産 | 価格DB → エリア別坪単価・月次推移グラフ |
| 経理 | 予実・経費内訳のグラフ |
| PMO | プロジェクト進捗・ポートフォリオ図 |
| Event Ops | 盆踊りチラシ・告知バナー・会場図の清書 |
| 秘書 | 資料に貼る図版・サムネ |

## 成果物の置き場

- データ可視化PNG: `docs/creative-visual/`
- 生成スクリプト・共通基盤: `tools/creative_visual/`
- デザイン画像: 用途に応じて提案（例: `apps/.../assets/`、`company/projects/<id>/assets/`）

## CEO 確認が必要

- 対外公開する図版・デザインの最終確定
- 個人情報を含むデータの可視化・外部送信
