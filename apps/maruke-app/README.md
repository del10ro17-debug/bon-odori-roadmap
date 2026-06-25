# まるつけ｜写真で答え合わせ

小学生の宿題を、親が写真を撮るだけで一瞬答え合わせできるスマホ向け Web アプリ（PWA）。

**ターゲット:** 中学受験家庭（小4〜6）の毎晩の丸つけ。塾・進研・Z会のプリント対応を目指す。

## しくみ

1. 子どもの答案（問題＋答え）をスマホで撮影
2. OpenAI Vision が設問ごとに読み取り・採点
3. `⭕️ / ❌ / 🟡要確認` と正解・ヒントを表示

### 採点の設計方針（誤採点を避ける）

- **解答ページを一緒に撮る**と、それを正解の根拠に優先（自分で解かない）→ 精度が最も高い
- 解答がない場合は AI が自力で解いて採点。**自信がないものは勝手に×にせず 🟡要確認**
- 記述問題は無理に○×せず、観点コメント＋解答例を提示
- 小5・小6はより精密なモデルで採点（環境変数で変更可）

## セットアップ

```bash
cd apps/maruke-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY を記入（無くてもデモモードで動作）
```

## 起動

### 同じ Wi-Fi のスマホ（LAN）

**Cmd + Shift + P** → `Tasks: Run Task` → **まるつけ: スマホ用起動 (LAN)**

または `open_maruke_app.command` をダブルクリック。

- PC: http://localhost:8010
- スマホ: `http://<MacのIP>:8010`

### 別 Wi-Fi・LTE から（トンネル）

`open_maruke_app_tunnel.command` をダブルクリック。

または **Tasks: Run Task** → **まるつけ: トンネル起動 (別Wi-Fi・LTE)**

ターミナルに `https://xxxx.trycloudflare.com` が表示されるので、iPhone の Safari で開く。
**共有 → ホーム画面に追加** でアプリアイコン化できる（PWA）。

- Mac が起動している間だけ有効（URL は毎回変わる）
- 初回は cloudflared を自動ダウンロード（数秒）

### 手動

```bash
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

- iPhone の HEIC はフロント側で自動 JPEG 変換

## ベータ公開（妻・友人に配る）

固定 URL で Web 公開する手順は **[DEPLOY.md](DEPLOY.md)** を参照。

```bash
brew install flyctl && fly auth login
cd apps/maruke-app && fly launch --no-deploy
fly secrets set OPENAI_API_KEY="sk-..." BETA_INVITE_CODE="合言葉"
fly deploy
```

## 構成

| ファイル | 役割 |
|---|---|
| `app.py` | FastAPI。`/api/grade` 採点API + 静的配信 |
| `grader.py` | OpenAI Vision 採点（Structured Outputs） |
| `static/index.html` | スマホUI（カメラ撮影・結果表示） |

## API

`POST /api/grade`（multipart/form-data）

| フィールド | 必須 | 説明 |
|---|---|---|
| `images` | ✅ | 答案画像（複数可） |
| `subject` | – | 教科（算数・国語など） |
| `grade_level` | – | 学年（1〜6） |
| `answer_key` | – | 解答ページ画像 |

`GET /api/health` … APIキー設定状況の確認

## 元プロジェクト

Codex で開発していた `~/Projects/maruke-app` を company-hq に移植・改善した版です。
