# まるつけ ベータ公開（妻・友人向け）

固定 URL で Web 公開する手順。おすすめは **Fly.io**（東京リージョン・HTTPS 自動）。

## ざっくり費用

| 項目 | 目安 |
|---|---|
| Fly.io ホスティング | 無料枠〜月 $5 程度（アクセス少なめベータ） |
| OpenAI API | 1回の採点 約 10〜50円（枚数・問題数による） |

## 1. Fly.io CLI

```bash
brew install flyctl
fly auth login
```

## 2. 初回セットアップ

```bash
cd apps/maruke-app
fly launch --no-deploy
# アプリ名: maruke-app（または任意）
# リージョン: Tokyo (nrt) を選ぶ
```

## 3. 秘密情報を設定

```bash
fly secrets set OPENAI_API_KEY="sk-..."
fly secrets set BETA_INVITE_CODE="家族に渡す合言葉"   # 例: maruke-sakakura-2026
```

`BETA_INVITE_CODE` を設定すると、合言葉を知っている人だけ使えます（API 料金の暴走防止）。

## 4. デプロイ

```bash
fly deploy
# またはリポジトリルートから
chmod +x tools/maruke_app/deploy-fly.sh
tools/maruke_app/deploy-fly.sh
```

## 5. 妻・友人に渡すもの

1. **URL** — `https://maruke-app.fly.dev`（アプリ名により変わる）
2. **招待コード** — `BETA_INVITE_CODE` に設定した合言葉
3. **使い方** — Safari で開く → ホーム画面に追加

## 運用

```bash
fly logs              # エラー確認
fly status            # URL 確認
fly secrets list      # 設定済み秘密情報
fly deploy            # コード更新後の再デプロイ
```

## ローカルで Docker 確認（任意）

```bash
cd apps/maruke-app
docker build -t maruke-app .
docker run --rm -p 8080:8080 \
  -e OPENAI_API_KEY="sk-..." \
  -e BETA_INVITE_CODE="test" \
  maruke-app
# http://localhost:8080
```

## 注意

- プリント写真は OpenAI に送信されます。ベータ参加者への説明を推奨
- 本格公開前に利用規約・プライバシーポリシーを整備
- 採点精度はベータ品質。誤採点は保護者確認前提
