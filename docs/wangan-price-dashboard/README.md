# 湾岸マンション売出価格ダッシュボード

## かんたんな使い方

リポジトリ直下の `open_wangan_dashboard.command` をダブルクリックします。

自動で以下を実行します。

1. `data/wangan_prices.sqlite` を確認
2. ダッシュボード用の `data.js` を生成
3. ブラウザで `index.html` を開く

## Webで共有する場合

GitHub Pagesで公開すると、ブラウザから以下のURLで開けます。

```text
https://del10ro17-debug.github.io/bon-odori-roadmap/wangan-price-dashboard/
```

公開前にGitHubのRepository Settings > PagesでSourceを `GitHub Actions` に設定します。公開用の `data.js` は `--public-safe` で生成し、メール本文由来の抜粋を外します。

## 画面でできること

- プロジェクト、エリア、街区、棟、間取り、面積、信頼度で絞り込み
- 売出価格中央値、坪単価中央値、値下げ件数の確認
- 面積と売出価格の散布図
- プロジェクト別、月別、街区・棟別の比較
- 表示中データのCSV出力

## 他マンションを追加する場合

SQLiteの `price_observations` に `project_name` が入っていれば、同じUIに自動で追加されます。

豊海などを追加する場合も、基本は以下の共通フィールドを増やすだけです。

- `project_name`
- `village_name`
- `building_code`
- `area`
- `room_type`
- `size_sqm`
- `price_jpy`
- `unit_price_per_tsubo_man`
