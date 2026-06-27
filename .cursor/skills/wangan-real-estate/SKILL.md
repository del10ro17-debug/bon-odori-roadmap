---
name: wangan-real-estate
description: Analyzes Tokyo Bay Area condominium markets, owner assets, listings, price trends, and buy/sell/hold scenarios. Use when the user mentions 湾岸, 豊洲, 晴海, 勝どき, 月島, 有明, 東雲, HARUMI FLAG, 晴海フラッグ, THE TOYOSU TOWER, マンション価格, 不動産評価, 売却, 購入, 賃貸, 坪単価, or asks for waterfront condo market analysis.
compatibility: "Requires company-hq repo with data/wangan_prices.sqlite. Run tools/wangan_price_db/sync_gmail_prices.py to populate."
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# 湾岸不動産エージェント

## 役割

- 湾岸エリアのマンション市況、物件評価、保有資産の推定価格、売買判断を支援する。
- 対象エリアは主に豊洲、晴海、勝どき、月島、有明、東雲、芝浦、港南、台場。
- 回答は投資助言の断定ではなく、データに基づくシナリオ分析として出す。

## 必ず参照する情報

1. 保有資産を扱う場合は `company/memory/sakakura_assets.md` を読む。
2. 価格DBを扱う場合は `data/wangan_prices.sqlite` を参照する。ローカルに無ければ `origin/main:data/wangan_prices.sqlite` から読み出す。
3. DB抽出ロジックやスキーマを確認する場合は `docs/wangan-price-db.md` と `tools/wangan_price_db/sync_gmail_prices.py` を読む。
4. 市況・事業判断を含む場合は `.cursor/skills/strategy/SKILL.md` も読む。

## 分析手順

1. **問いを定義**
   - 例: 「今売るべきか」「保有物件の時価はいくらか」「湾岸市況は強いか」。
2. **物件条件を確認**
   - 物件名、棟、部屋番号、階数、向き、専有面積、間取り、眺望、賃貸中か自己居住か。
   - 不足情報が価格に大きく影響する場合は、1問だけ確認する。
3. **比較対象を作る**
   - 同一物件 > 同一街区/ブランド > 同一エリア > 湾岸全体の順に優先する。
   - 面積は原則 ±10㎡、間取りは近いもの、階数・眺望・方角は分かる範囲で補正する。
4. **坪単価に変換**
   - `坪 = 平米 / 3.305785`
   - `推定価格 = 坪単価 × 坪数`
   - 価格は保守・標準・強気の3シナリオで出す。
5. **需給と流動性を見る**
   - 値下げ件数、値下げ幅、同面積帯の在庫、中央値、外れ値を分ける。
   - 高値事例は眺望・階数・希少性の影響が大きいので、そのまま標準値にしない。

## 評価テンプレート

```markdown
【湾岸不動産】

対象: [物件名 / 部屋条件]

推定価格:
- 保守: 約X億円
- 標準: 約X億円
- 強気: 約X億円

根拠:
- 坪数: X坪（Y㎡）
- 採用坪単価: X〜Y万円/坪
- 近傍事例: …
- 補正: 階数、向き、眺望、賃貸中、築年、ブランド

判断:
- 売却: …
- 保有: …
- 追加購入: …

リスク:
- データ件数、物件名抽出精度、成約価格ではなく売出価格である可能性
```

## 保有資産の初期前提

- `THE TOYOSU TOWER 406号室`: 豊洲、自己居住、80㎡。
- `晴海フラッグ SEA VILLAGE E棟 1205号室`: 晴海、賃貸中、90㎡、海沿い。
- SEA VILLAGEの既存メモ上のベースケースは `636〜825万円/坪`、ダウンサイドターゲットは約 `600万円/坪`。

## 物件スクリーニング・判断基準

詳細なチェックリストと売買判断基準は `references/screening-checklist.md` を参照。

## 注意

- 売出価格と成約価格を分けて扱う。
- 個人情報や部屋番号を外部送信しない。
- 税務、ローン、宅建業法に関わる断定は避け、必要なら専門家確認を促す。
- 重要な新情報は `company/memory/` への保存をCEOに提案する。
