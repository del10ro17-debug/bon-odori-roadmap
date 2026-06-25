# Render 固定 URL（カード不要）

Fly より手軽。**クレカ不要**で固定 URL がもらえます。

**固定 URL 例:** `https://maruke-app.onrender.com`

## 制限（無料枠）

- 15分アクセスがないとスリープ → 初回 **30〜60秒** かかる
- RAM 512MB（このアプリで足りる）

---

## 手順 A: ダッシュボード（おすすめ・5分）

1. https://render.com で **GitHub ログイン**（カード不要）
2. **New +** → **Blueprint**
3. このリポジトリ `company-hq` を接続（初回は GitHub 連携）
4. `render.yaml` が検出される → **Apply**
5. 環境変数を設定:
   - `OPENAI_API_KEY` = あなたのキー
   - `BETA_INVITE_CODE` = 友達用合言葉（任意）
6. デプロイ完了後、表示される URL を友達に共有

`render.yaml` は `apps/maruke-app/` 用に設定済み。

### リポジトリが GitHub にない場合

1. GitHub に `company-hq` を push（private でも可）
2. 上の手順 2 から

---

## 手順 B: Render CLI

```bash
# CLI インストール（済ならスキップ）
curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

render login
# ダッシュボードで認証コードを承認

cd apps/maruke-app
render blueprint launch
```

---

## 友達に渡すもの

- **URL:** `https://maruke-app.onrender.com`（サービス名で変わる）
- **招待コード**（設定した場合）

---

## トラブル

| 症状 | 対処 |
|------|------|
| 最初だけ遅い | スリープ復帰。有料 $7/月 で常時起動 |
| ビルド失敗 | Render ログで Docker エラー確認 |
| 502 | `OPENAI_API_KEY` 未設定 |
