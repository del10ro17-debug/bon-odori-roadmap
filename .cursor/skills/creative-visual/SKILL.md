---
name: creative-visual
description: >-
  Produces images and data visualizations: charts/graphs from real data
  (matplotlib / Cursor Canvas) and design assets (flyers, icons, SNS images,
  mockups) via image generation. Use when the user mentions グラフ, チャート,
  可視化, 図, 絵, イラスト, ロゴ, チラシ, アイコン, バナー, モックアップ, ダッシュボード画像, or asks to
  visualize numbers / make a picture.
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

## グラフの選び方（デジタル庁ガイドブック準拠）

| 伝えたいこと | グラフ | 補足 |
|---|---|---|
| 時間変化・傾向 | 折れ線 | 横軸は時間。系列名は線の近くに |
| 数量の比較 | 棒（分類軸×数量軸） | 複数系列は集合棒、構成比は積み上げ棒 |
| 時間変化＋構成比 | 面（積み上げ） | 構成比不要なら折れ線 |
| 構成比 | 円／ドーナツ | 全体総量が明確な時のみ。多くは棒の方が正確 |
| 一覧・多項目 | 表 | 値に色・図形を併用可 |

## 設計原則（必ず守る）

**知りたいことを知れる**
- シンプルにする（不要なデータ・装飾・説明を削る）
- 意味のある順列にする（数量の大小順など。「あいうえお順」など無意味な並びは避ける）
- 強弱をつける（注目させたい系列だけ色・太さを変える）
- 待たせない（重い処理を避ける）

**誤解を生まない**
- タイトルにデータ種別を明記（例「国産自動車の出荷台数（月次推移）」）
- データを定義する（対象・単位・更新時点）
- 表現を歪曲しない（**棒グラフの原点は0**、軸範囲を恣意的にしない）
- メタ情報を記載（出典・時点・注釈）→ `chartkit` の `source=` 引数で右下に付与

## カラーパレット（デジタル庁デザインシステム）

`chartkit` に内蔵済み。手で色指定する場合の基準：

- 単系列の既定: `PRIMARY = #0017C1`（Blue 900）
- 多系列: `DA_PALETTE`（Blue/Orange/Green/Cyan/Red/Gray/LightBlue の 600 系）
- 増減表現: `POSITIVE = #197A4B` / `NEGATIVE = #CE0000`
- **色数は 1〜5 に絞る**。背景とのコントラスト比は 3:1 以上（満たせなければ数値併記、文字は 4.5:1）

## アクセシビリティ

- **色のみで識別しない**：数値を併記し、折れ線はマーカー形状も変える（`chartkit` が自動対応）
- 白黒印刷でも伝わるか確認
- レポート公開時は、要約テキストと元データ（CSV等）も添える

## 仕上げチェックリスト（出力前に確認）

- [ ] タイトルにデータ種別（月次推移・累計など）が入っているか
- [ ] 棒グラフの原点は0か／軸を歪めていないか
- [ ] 色数は1〜5色に絞れているか／色だけに依存していないか（数値併記）
- [ ] グリッド・枠線・装飾（3D・影）を最小限にしたか
- [ ] 凡例はグラフに隣接し、順序が対応しているか
- [ ] 出典・時点（メタ情報）を記載したか（`source=`）
- [ ] 重要な指標から詳細へ、左上→右下に並んでいるか（資料/ダッシュボード時）

## レイアウト（複数グラフをまとめる資料・ダッシュボード）

- 視線に沿って **左上＝全体指標 → 右下＝詳細** に配置
- フィルターは上部か左部、影響を受けるグラフはその下／右
- 16:9・縦横2〜6分割グリッドを基準にそろえる

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
