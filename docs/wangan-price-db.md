# 湾岸マンション価格DB

Gmailに毎週届く湾岸マンション関連メールを取得し、価格情報をSQLiteに蓄積する仕組みです。

## 構成

- 同期スクリプト: `tools/wangan_price_db/sync_gmail_prices.py`
- SQLite DB: `data/wangan_prices.sqlite`
- 定期実行: `.github/workflows/wangan-price-db.yml`
- 実行タイミング: 毎週金曜 18:00 JST

## DBテーブル

`gmail_messages`

- `message_id`: GmailメッセージID
- `thread_id`: GmailスレッドID
- `received_at`: メール受信日時
- `from_email`: 送信元
- `subject`: 件名
- `snippet`: Gmail snippet
- `body_text`: 抽出元の本文

`price_observations`

- `observation_id`: 重複防止用ID
- `message_id`: 元メールID
- `observed_at`: 観測日時
- `property_name`: 物件名候補
- `area`: エリア候補
- `room_type`: 間取り候補
- `floor`: 階数候補
- `size_sqm`: 平米数候補
- `price_jpy`: 価格
- `unit_price_per_tsubo`: 坪単価候補
- `source_text`: 抽出元テキスト
- `confidence`: 抽出信頼度

## GitHub設定

Repository secrets に以下を登録します。

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Repository variables は任意です。

- `WANGAN_GMAIL_QUERY`
  - 例: `from:example@example.com ("湾岸" OR "豊洲" OR "晴海" OR "勝どき") newer_than:14d`
  - 未設定時: `("湾岸" OR "豊洲" OR "晴海" OR "勝どき" OR "月島" OR "有明" OR "東雲") newer_than:14d`
- `WANGAN_GMAIL_MAX_RESULTS`
  - 未設定時: `50`

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
python tools/wangan_price_db/get_refresh_token.py
```

ブラウザでGoogleアカウントにログインし、表示された `GOOGLE_REFRESH_TOKEN` をGitHub Secretsに登録します。

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tools/wangan_price_db/requirements.txt

export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
export GOOGLE_REFRESH_TOKEN="..."

python tools/wangan_price_db/sync_gmail_prices.py \
  --db data/wangan_prices.sqlite \
  --query '("湾岸" OR "豊洲" OR "晴海" OR "勝どき") newer_than:14d'
```

書き込み前に抽出結果だけ見る場合:

```bash
python tools/wangan_price_db/sync_gmail_prices.py --dry-run
```

## 確認クエリ

```bash
sqlite3 data/wangan_prices.sqlite \
  "SELECT observed_at, area, property_name, room_type, size_sqm, price_jpy, unit_price_per_tsubo, confidence FROM price_observations ORDER BY observed_at DESC LIMIT 20;"
```

## 運用メモ

- 初期の抽出は正規表現ベースです。メール本文の形式が分かれば、物件名や坪単価の抽出精度を上げられます。
- GitHub ActionsはDB更新があった場合だけ `data/wangan_prices.sqlite` を自動コミットします。
- Gmail本文には個人情報が含まれる可能性があります。必要なら `body_text` と `source_text` の保存範囲を絞ってください。
