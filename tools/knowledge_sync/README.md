# Knowledge Sync — Obsidian ハブ連携

company-hq と Obsidian vault をつなぐ同期・セットアップ手順。

## クイックセットアップ

```bash
# 1. obsidian-sync.env が無ければ cursor-sync から NOTION_TOKEN をコピー
bash tools/knowledge_sync/setup-obsidian-env.sh

# 2. Notion daily fetch を手動テスト
node "/Users/sho_sakakura/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian/scripts/daily-notion-fetch.js"

# 3. Cursor daily → Obsidian .raw/ を手動テスト
node ~/.claude/cursor-sync/cursor-daily-sync.js

# 4. Cursor 会話 → Obsidian（日次 08:30、手動テスト）
bash tools/knowledge_sync/run-cursor-obsidian-sync.sh

# 5. 転職Gmail → Obsidian .raw/（OAuth 設定後）
python3 tools/knowledge_sync/sync_career_gmail.py
```

## Cursor 会話 → Obsidian（日次）

**LaunchAgent `com.user.cursor-daily-sync`（08:30 JST）** が以下をまとめて実行:

- agent-transcripts → `wiki/sources/cursor/` + `.raw/cursor-chat-*.md` + `hot.md` の `cursor:` 行
- `.cursor/plans` 変更 + git コミット → Daily Log 用 digest

手動（今すぐ同期）:

```bash
# 直近30日（日次ジョブと同じ範囲）
bash tools/knowledge_sync/run-cursor-obsidian-sync.sh --days 30

# 初回バックフィル（強制再書き込み）
bash tools/knowledge_sync/run-cursor-obsidian-sync.sh --days 30 --force
```

旧 30分 LaunchAgent が残っている場合:

```bash
bash tools/knowledge_sync/install-cursor-transcript-sync.sh
```

## 転職 Gmail 取り込み

### 正: Cowork + Gmail MCP（CEO が使用中）

Cursor から Gmail は読めない。**Cowork で Gmail MCP を起動したうえで**、取り込みプロンプトを実行する。

手順とコピペ用プロンプト: [cowork-gmail-career-ingest.md](cowork-gmail-career-ingest.md)

要点: メールを読むだけでは wiki は更新されない。**同セッションで `.raw/` + `転職活動.md` + `hot.md` まで Write する**。

### 予備: OAuth スクリプト（Cowork 無し / 自動化用）

Gmail readonly OAuth を `~/Projects/wangan-db/.env` または `~/.claude/obsidian-sync.env` に置く:

```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

初回トークン取得（ブラウザで同意）:

```bash
cd company-hq
export GOOGLE_CLIENT_ID=...
export GOOGLE_CLIENT_SECRET=...
python3 tools/wangan_price_db/get_refresh_token.py
# 表示された refresh token を .env に保存
```

手動テスト:

```bash
python3 tools/knowledge_sync/sync_career_gmail.py
# → Obsidian .raw/email-notion-*.md が作成される
# → auto-ingest が wiki/sources/ へ昇格（LaunchAgent 稼働中なら自動）
```

LaunchAgent 登録（毎朝 8:15 JST）:

```bash
cp tools/knowledge_sync/com.user.career-gmail-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.career-gmail-sync.plist
launchctl start com.user.career-gmail-sync
```

ログ: `/tmp/career-gmail-sync.log`, `/tmp/career-gmail-sync-error.log`

## Notion → Obsidian（議事録・タスク・予定）

会社HQ の Notion DB を `.raw/` にミラーする。**議事録DB等は Notion 側で claude-obsidian 連携への共有が必要。**

手順: [notion-to-obsidian-setup.md](notion-to-obsidian-setup.md)

Custom Agent（日次振り分け）: [notion-custom-agent-daily-router.md](notion-custom-agent-daily-router.md)

```bash
# 初回フル移行
bash tools/knowledge_sync/run-notion-company-sync.sh --full

# 議事録だけ
bash tools/knowledge_sync/run-notion-company-sync.sh --full --db meetings
```

LaunchAgent（08:10 JST）:

```bash
cp tools/knowledge_sync/com.user.notion-company-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.notion-company-sync.plist
```

## LaunchAgent 一覧

| Label | スクリプト |
|-------|-----------|
| `com.user.claude-obsidian-daily` | `scripts/daily-notion-fetch.js` |
| `com.user.notion-company-sync` | `tools/knowledge_sync/run-notion-company-sync.sh` |
| `com.user.cursor-daily-sync` | `~/.claude/cursor-sync/cursor-daily-sync.js`（08:30・transcript 含む） |
| `com.user.claude-obsidian-ingest` | `~/bin/auto-ingest.js` |
| `com.user.career-gmail-sync` | `tools/knowledge_sync/run-career-gmail-sync.sh` |

ログ: `/tmp/notion-daily-fetch.log`, `/tmp/cursor-daily-sync.log`, `/tmp/career-gmail-sync.log`

## トラブルシュート

| 症状 | 原因 | 対処 |
|------|------|------|
| `NOTION_TOKEN is required` | `obsidian-sync.env` 未作成 | `setup-obsidian-env.sh` |
| `.raw/` に notion-daily が無い | 当日 Notion Daily Log 未記入 | Notion に日次エントリ作成 |
| Cursor 議論が wiki に無い | 日次 08:30 前 / LaunchAgent 停止 | `run-cursor-obsidian-sync.sh` で手動実行 |
| Notion 転職メールが wiki に無い | Gmail OAuth 未設定 | `sync_career_gmail.py` + LaunchAgent |
| claude.ai が止まる | API クレジット / 手動棚卸し | `wiki/sources/claude-ai-recents-*.md` を週次更新 |

## 正本マップ

[docs/knowledge-ssot.md](../../docs/knowledge-ssot.md)
