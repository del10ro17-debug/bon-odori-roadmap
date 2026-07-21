# デスクトップ × クラウド開発環境

デスクトップの Cursor を主戦場にしつつ、外出先やブラウザから Cloud Agent で実装・チェックできる構成です。

## 役割分担

| 場所 | 向いていること | 向かないこと |
|------|----------------|--------------|
| **デスクトップ Cursor** | UI 確認、Obsidian wiki、秘密情報の編集、手元デモ、日常の小修正 | 長時間の無人実装を張り付きで見守ること |
| **Cloud Agent** | 実装・リファクタ・テスト・PR、外出先でのチェック／続き | Mac 上の Obsidian 直編集、ローカル限定ツール |
| **GitHub Actions** | PR の最終ゲート（両環境共通） | 対話的な設計判断 |

共通の正本は **Git**（コード・`status.md`・スキル・本ドキュメント）です。

## 構成ファイル（リポジトリ内）

| ファイル | 役割 |
|----------|------|
| [`.cursor/environment.json`](../.cursor/environment.json) | Cloud Agent が使う環境定義 |
| [`.cursor/Dockerfile`](../.cursor/Dockerfile) | Python 3 / Node 22 / gh などシステム層 |
| [`.cursor/cloud-install.sh`](../.cursor/cloud-install.sh) | 依存の冪等インストール（起動時 `install`） |

環境の解決順（Cursor 公式）:

1. リポジトリの `.cursor/environment.json`（最優先）
2. 個人の保存 Environment
3. チームの保存 Environment

## 初回セットアップ（CEO・一度だけ）

1. このブランチ／`main` に上記ファイルが入っていることを確認
2. [Cloud Agents ダッシュボード](https://cursor.com/dashboard?tab=cloud-agents) でこのリポジトリの Environment を開く
3. **Secrets** に必要な値だけ追加（リポジトリには書かない）
   - `OPENAI_API_KEY` … まるつけ実採点テスト時
   - `BETA_INVITE_CODE` … 必要なら
4. 新しい Cloud Agent を **このリポジトリのブランチ** から起動し、install が通ることを確認
5. 問題なければ snapshot を保存（次回起動が速くなる）

Desktop 側の既存手順（`apps/maruke-app/.venv` など）はそのまま使えます。クラウドはリポジトリ直下の `.venv` を使います（`.gitignore` 済み）。

## 日常の使い方

### デスクトップ（主）

いつもどおりローカルで開いて編集・実行。

```bash
cd apps/maruke-app
source .venv/bin/activate   # なければ README の venv 作成
uvicorn app:app --host 0.0.0.0 --port 8010
```

### クラウド（外から実装・チェック）

1. cursor.com または Desktop の Agents から Cloud Agent を起動
2. 依頼例:
   - `@it apps/maruke-app のこのバグを直してテストして PR まで`
   - `@maruke-light-chat @company/projects/maruke-app/AGENT_CONTEXT.md を前提に。…`
3. Agent はブランチ作成 → 実装 → 検証 → PR まで進める
4. Desktop に戻ったら PR をレビューし、必要なら UI だけ手元確認

クラウドでアプリを起動して確認する例:

```bash
source .venv/bin/activate
cd apps/maruke-app
uvicorn app:app --host 0.0.0.0 --port 8010
```

## ナレッジの両立

| 情報 | Desktop | Cloud |
|------|---------|-------|
| コード・案件 `status.md` | Git | Git（同じ） |
| Obsidian wiki / `hot.md` | 直接 Read/Edit | **不可** → `status.md` / `AGENT_CONTEXT.md` / Notion MCP を使う |
| Notion タスク・議事 | Notion MCP | 要認証（Dashboard で MCP 接続） |
| 会話の長期保存 | cursor-daily-sync → Obsidian | 同上（ローカル側ジョブ） |

クラウド作業の依頼には、できるだけ `@*-light-chat` と `AGENT_CONTEXT.md` を付けて文脈を Git 側に寄せてください。

## 検証コマンド（両環境共通）

```bash
# 依存が入っているか
source .venv/bin/activate   # cloud / または apps/maruke-app/.venv
python -c "import fastapi, uvicorn, PIL, fitz, matplotlib; print('ok')"

# まるつけ（API キー無しならデモモード）
cd apps/maruke-app && uvicorn app:app --host 127.0.0.1 --port 8010
```

## 更新のしかた

- システムツールを足す → `.cursor/Dockerfile` を編集 → push → 次回 Cloud Agent が再ビルド
- Python/Node 依存を足す → 各 `requirements.txt` または `cloud-install.sh` → push（`install` が差分適用）
- 運用ルールを変える → このドキュメントと `AGENTS.md` の Cloud 節を更新

## 関連

- [AGENTS.md](../AGENTS.md) — Cursor Cloud specific instructions
- [agent-playbook.md](agent-playbook.md) — チャット運用
- [knowledge-ssot.md](knowledge-ssot.md) — 正本マップ
