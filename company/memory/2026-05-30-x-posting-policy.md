# X投稿エージェント 運用方針（出典・グラフ）

> **決定ログ（2026-05-30）。** 正本は Git `company/memory/` このファイル + 実装側。横断参照は Obsidian wiki。

- 日付: 2026-05-30
- 決定者: CEO
- 内容: X自動投稿エージェント（`wangan-agent`）における「出典の明記」と「グラフのデータ源」の運用ルールを確定する。

## 方針（厳守）

1. **出典の明記**
   - 投稿で URL・他者の情報・データ・記事を引用／参照したら、**必ず出典（URL＋媒体名）を `sources` に残す**。
   - 出典を書けない引用・数値は投稿に載せない。
   - web_search で得た事実は、対応する出典URLを必ず残す。

2. **グラフは個人DBから作成**
   - データをグラフにするときは、**CEO 個人の価格DB** から集計する。
   - データ元: `docs/wangan-price-dashboard/data.js`（湾岸価格ダッシュボード）。
   - **LLM に数値は作らせない**（捏造防止）。集計はコードで行う。

3. **グラフの出典表記**
   - グラフには「**個人データより作成**（湾岸価格DB ◯◯時点）」と出典を明記する。

## 適用範囲

- 第一に `wangan-agent`（湾岸ウォッチャー）。X事業の投稿生成・グラフ生成すべてに適用。
- 数値グラフ全般は creative-visual の鉄則（コード描画・原点0・数値併記・出典）も併せて守る。

## 実装反映先（IT）

- `~/Projects/wangan-agent/services/personalData.js` — 個人価格DBから月次中央値・エリア比較を集計
- `~/Projects/wangan-agent/services/mediaFactory.js` — 湾岸グラフは個人DB由来のみ
- `~/Projects/wangan-agent/services/domains.js` — 出典必須ルール、`chart_area` ヒント（数値chartは廃止）
- データ元パスは `WANGAN_PRICE_DATA_PATH`（既定 `~/company-hq/docs/wangan-price-dashboard/data.js`）

## 関連

- X事業 統合メモ: `company/memory/2026-05-17-x-business.md`
- 案件進捗: `company/projects/x-business/status.md`
