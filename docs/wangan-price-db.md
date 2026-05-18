# 湾岸マンション価格DB

Gmailに毎週届く湾岸マンション関連メールを取得し、価格情報をSQLiteに蓄積する仕組みです。

## 構成

- 同期スクリプト: `tools/wangan_price_db/sync_gmail_prices.py`
- HARUMI FLAG分析: `tools/wangan_price_db/analyze_harumi_flag.py`
- ダッシュボードデータ出力: `tools/wangan_price_db/export_dashboard_data.py`
- SQLite DB: `data/wangan_prices.sqlite`
- 静的ダッシュボード: `docs/wangan-price-dashboard/index.html`
- 定期実行: `.github/workflows/wangan-price-db.yml`
- データソース方針: `docs/wangan-price-source-policy.md`
- 実行タイミング: 毎週金曜 18:00 JST
- 取得条件の初期値: `subject:"湾岸マンション価格ナビ" newer_than:180d`
- 取得件数の初期値: `500`

## DBテーブル

このDBは、正規表現で取り切れない項目があっても後から再解析できるように、メール本文の全行と抽出元テキストを保存します。

`gmail_messages`

- `message_id`: GmailメッセージID
- `thread_id`: GmailスレッドID
- `received_at`: メール受信日時
- `from_email`: 送信元
- `subject`: 件名
- `snippet`: Gmail snippet
- `body_text`: 抽出元の本文

`email_lines`

- `line_id`: 行ID
- `message_id`: 元メールID
- `line_index`: 本文内の行番号
- `line_text`: 正規化した行テキスト
- `line_hash`: 行内容のハッシュ

`price_observations`

- `observation_id`: 重複防止用ID
- `message_id`: 元メールID
- `observed_at`: 観測日時
- `source_type`: 抽出元の種類
- `row_index`: 抽出元の行番号
- `property_name`: 物件名候補
- `building_name`: 建物名候補
- `project_name`: 正規化したプロジェクト名（例: `HARUMI FLAG`）
- `village_name`: 正規化した街区名（例: `SEA VILLAGE`）
- `building_code`: 正規化した棟名（例: `E棟`）
- `area`: エリア候補
- `room_type`: 間取り候補
- `floor`: 階数候補
- `size_sqm`: 平米数候補
- `price_jpy`: 価格
- `previous_price_jpy`: 価格改定前の価格候補
- `price_change_jpy`: 価格改定額候補
- `unit_price_per_tsubo_man`: 坪単価候補（万円/坪）
- `unit_price_per_tsubo_jpy`: 坪単価候補（円/坪）
- `direction`: 方角候補
- `raw_line`: 抽出元の行
- `source_text`: 抽出元テキスト
- `parsed_fields_json`: パースした全フィールドのJSON
- `confidence`: 抽出信頼度

## GitHub設定

Repository secrets に以下を登録します。

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Repository variables は任意です。

- `WANGAN_GMAIL_QUERY`
  - 例: `subject:"湾岸マンション価格ナビ" newer_than:180d`
  - 未設定時: `subject:"湾岸マンション価格ナビ" newer_than:180d`
- `WANGAN_GMAIL_MAX_RESULTS`
  - 未設定時: `500`

## 過去分バックフィル

初回や分析前に過去数ヶ月分を取り込む場合は、GitHub Actionsの `Update Wangan Price DB` を手動実行します。

推奨入力:

- `query`: `subject:"湾岸マンション価格ナビ" newer_than:180d`
- `max_results`: `500`

ノイズメールを避けるため、通常は件名を `湾岸マンション価格ナビ` に絞ります。期間を広げる場合は `newer_than:365d` のように変更できます。

## Gmail OAuth準備

1. Google Cloud Consoleでプロジェクトを作成します。
2. Gmail APIを有効化します。
3. OAuth consent screenを設定します。
4. OAuth client IDを作成します。
5. スコープは `https://www.googleapis.com/auth/gmail.readonly` のみにします。
6. 初回だけローカルでrefresh tokenを取得し、GitHub Secretsへ登録します。

refresh tokenの取得:

```bash
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
python3 tools/wangan_price_db/get_refresh_token.py
```

ブラウザでGoogleアカウントにログインし、表示された `GOOGLE_REFRESH_TOKEN` をGitHub Secretsに登録します。

## ローカル実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/wangan_price_db/requirements.txt

export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
export GOOGLE_REFRESH_TOKEN="..."

python3 tools/wangan_price_db/sync_gmail_prices.py \
  --db data/wangan_prices.sqlite \
  --query 'subject:"湾岸マンション価格ナビ" newer_than:180d' \
  --max-results 500
```

書き込み前に抽出結果だけ見る場合:

```bash
python3 tools/wangan_price_db/sync_gmail_prices.py --dry-run
```

既存DBをローカルに復元する場合:

```bash
mkdir -p data
git show origin/main:data/wangan_prices.sqlite > data/wangan_prices.sqlite
```

DBが存在しない場合は、上記のローカル実行またはGitHub Actionsの手動実行で新規作成します。

## 確認クエリ

```bash
sqlite3 data/wangan_prices.sqlite \
  "SELECT observed_at, property_name, room_type, size_sqm, price_jpy, previous_price_jpy, price_change_jpy, unit_price_per_tsubo_man, direction, confidence FROM price_observations ORDER BY observed_at DESC LIMIT 20;"
```

## HARUMI FLAG分析

HARUMI FLAGに絞った分析:

```bash
python3 tools/wangan_price_db/analyze_harumi_flag.py \
  --db data/wangan_prices.sqlite
```

主な出力:

- 観測件数、価格レンジ、坪単価レンジ、中央値
- 街区・棟別の件数、価格中央値、坪単価中央値
- 面積帯別の件数、価格中央値、坪単価中央値
- 値下げ観測件数、値下げ額中央値
- 直近の高信頼度観測

`price_observations` には抽出元テキストも保存されます。分析値が外れ値に見える場合は、`source_text` と `raw_line` を確認してください。

## Webダッシュボード

ターミナル操作を避けたい場合は、リポジトリ直下の `open_wangan_dashboard.command` をダブルクリックします。

このファイルは次の処理を自動で行います。

1. `data/wangan_prices.sqlite` がなければ `origin/main` から復元を試す
2. SQLiteから `docs/wangan-price-dashboard/data.js` を生成する
3. `docs/wangan-price-dashboard/index.html` をブラウザで開く

SQLiteから静的Webページ用の `data.js` を生成します。

```bash
python3 tools/wangan_price_db/export_dashboard_data.py \
  --db data/wangan_prices.sqlite \
  --output docs/wangan-price-dashboard/data.js
```

特定プロジェクトだけに絞る場合:

```bash
python3 tools/wangan_price_db/export_dashboard_data.py \
  --db data/wangan_prices.sqlite \
  --output docs/wangan-price-dashboard/data.js \
  --project "HARUMI FLAG"
```

出力後、`docs/wangan-price-dashboard/index.html` をブラウザで開きます。`docs/index.html` からもリンクしています。

ダッシュボードの設計:

- `projectName` を主キーに近い分析軸として扱うため、HARUMI FLAG以外の豊海・勝どき・豊洲物件も同じUIに追加できます。
- `villageName`, `buildingCode`, `area`, `roomType`, `sizeSqm`, `priceJpy`, `unitPricePerTsuboMan` を共通フィールドとして表示・フィルタします。
- ブラウザ側にSQLiteやGmail認証情報は持たせず、必要な観測値だけを `data.js` に書き出します。
- `sourceExcerpt` は確認用の短い抜粋だけにし、個人情報やメール本文の過剰な露出を避けます。

## Web公開

GitHub Pagesで `docs/` 配下を公開します。公開用ワークフローは `.github/workflows/pages.yml` です。

公開手順:

1. GitHubのRepository Settings > PagesでSourceを `GitHub Actions` に設定します。
2. 変更を `main` に反映します。
3. `Publish Web Pages` workflow が実行されます。
4. 公開URLの末尾に `/wangan-price-dashboard/` を付けて開きます。

このリポジトリの想定URL:

```text
https://del10ro17-debug.github.io/bon-odori-roadmap/wangan-price-dashboard/
```

公開データ生成時は `--public-safe` を付けます。これにより、メール本文由来の `rawLine` と `sourceExcerpt` は公開用 `data.js` から除外されます。

## 外部掲載サイトの扱い

SUUMOなどの掲載サイトは、利用規約、robots.txt、サーバー負荷への配慮が必要です。このDBの初期運用では、外部サイトの自動巡回スクレイピングを前提にしません。

取り込み候補:

- Gmailで届く価格アラートや市場レポート
- 手動確認した公開掲載情報の控え
- 利用規約上許可されたAPI、CSV、データサービス

外部掲載情報を取り込む場合は、観測日、出典名、出典URL、売出価格であることを保存し、取得データを再配布しない運用にします。

## 運用メモ

- `email_lines` と `parsed_fields_json` があるため、抽出ロジックを改善した後に過去メールを再解析できます。
- 価格行は、面積・間取り・現在価格・旧価格・価格改定額・坪単価・方角を優先して抽出します。
- HARUMI FLAGは `project_name`, `village_name`, `building_code` に正規化して保存します。
- GitHub ActionsはDB更新があった場合だけ `data/wangan_prices.sqlite` を自動コミットします。
- Gmail本文には個人情報が含まれる可能性があります。必要なら `body_text` と `source_text` の保存範囲を絞ってください。
