# 湾岸マンション価格DB

Gmailに毎週届く湾岸マンション関連メールを取得し、価格情報をSQLiteに蓄積する仕組みです。

## 構成

- 同期スクリプト: `tools/wangan_price_db/sync_gmail_prices.py`
- SQLite DB: `data/wangan_prices.sqlite`
- 定期実行: `.github/workflows/wangan-price-db.yml`
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

## 確認クエリ

```bash
sqlite3 data/wangan_prices.sqlite \
  "SELECT observed_at, property_name, room_type, size_sqm, price_jpy, previous_price_jpy, price_change_jpy, unit_price_per_tsubo_man, direction, confidence FROM price_observations ORDER BY observed_at DESC LIMIT 20;"
```

## 運用メモ

- `email_lines` と `parsed_fields_json` があるため、抽出ロジックを改善した後に過去メールを再解析できます。
- 価格行は、面積・間取り・現在価格・旧価格・価格改定額・坪単価・方角を優先して抽出します。
- GitHub ActionsはDB更新があった場合だけ `data/wangan_prices.sqlite` を自動コミットします。
- Gmail本文には個人情報が含まれる可能性があります。必要なら `body_text` と `source_text` の保存範囲を絞ってください。
