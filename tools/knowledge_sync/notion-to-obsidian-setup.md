# Notion → Obsidian 同期セットアップ

会社HQの Notion DB を Obsidian `.raw/` に自動ミラーし、auto-ingest が wiki に昇格するパイプ。

## 前提

- Notion API 連携名: **claude-obsidian**
- トークン: `~/.claude/obsidian-sync.env` の `NOTION_TOKEN`
- 同期スクリプト: Obsidian `scripts/notion-company-sync.js`

## 1. Notion 側の共有（必須・1回だけ）

現状、API 連携がアクセスできるのは **Daily Claude Log のみ** です。  
議事録・タスク・予定を同期するには、各 DB を連携に共有してください。

1. Notion で [会社HQ](https://www.notion.so/3633d2ab617d81af81f3e2c548bcfbb2) を開く
2. 右上 `...` → **Connections** → **claude-obsidian** を追加
   - または各 DB ページで同様に Connections から追加
3. 対象 DB（**各 DB ページで個別に** Connections 追加）:
   - [議事録](https://www.notion.so/a755adb2c9584da08c3cd009f95bf56a)
   - [キャディ 議事録](https://www.notion.so/dba74b1e1efa418881bfcac890e109da)
   - [プライベート議事録](https://www.notion.so/35acab82cc4b45bd970a3dab7d1f51fa)
   - [タスク](https://www.notion.so/854bb7ac1e7447588275960c4601f11e)
   - [予定](https://www.notion.so/5534fbf1a2ec4e41b1712f775e425b50)
   - [選考パイプライン](https://app.notion.com/p/a3ff6d2f060c4d589aeb8d5cc0661317)（Claude Context Hub）

共有後、接続テスト:

```bash
bash /Users/sho_sakakura/company-hq/tools/knowledge_sync/run-notion-company-sync.sh --db meetings
```

`[skip]` が出なければ OK。

## 2. 初回フル移行（過去分まとめて）

```bash
# 議事録を全件（または直近90日）
bash tools/knowledge_sync/run-notion-company-sync.sh --full --db meetings

# 全会社HQ DB（議事録・タスク・予定・Daily Log）
bash tools/knowledge_sync/run-notion-company-sync.sh --full
```

出力先: Obsidian `.raw/`

| DB | ファイル名 |
|----|-----------|
| 議事録 | `notion-meeting-{date}-{slug}-{id8}.md` |
| キャディ 議事録 | `notion-caddi-meeting-{date}-{slug}-{id8}.md` |
| プライベート議事録 | `notion-private-meeting-{date}-{slug}-{id8}.md` |
| タスク | `notion-tasks-{date}.md`（日次スナップショット） |
| 予定 | `notion-schedule-{date}.md`（日次スナップショット） |
| Daily Log | `notion-daily-{date}-{slug}-{id8}.md` |
| 選考パイプライン | `notion-career-pipeline-{date}-{slug}-{id8}.md` |

Custom Agent 設定: [notion-custom-agent-daily-router.md](notion-custom-agent-daily-router.md)

## 3. 毎朝の自動同期（LaunchAgent）

```bash
cp tools/knowledge_sync/com.user.notion-company-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.notion-company-sync.plist
launchctl start com.user.notion-company-sync
```

- 時刻: **08:10 JST**（Daily Log fetch 08:00 の直後）
- ログ: `/tmp/notion-company-sync.log`
- 差分: `last_edited_time` で変更ページのみ再取得（`--full` なし）

## 4. Obsidian wiki への昇格

`.raw/` にファイルが追加されると `com.user.claude-obsidian-ingest`（auto-ingest）が `ingest` を実行し、wiki に反映します。

手動で ingest したい場合（Obsidian vault 直下）:

```bash
cd "/Users/sho_sakakura/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian"
claude -p "ingest notion-meeting-2026-05-29-*.md" --dangerously-skip-permissions
```

## 5. トラブルシュート

| 症状 | 対処 |
|------|------|
| `Could not find database` | 該当 DB を claude-obsidian 連携に共有 |
| `.raw/` にファイルはあるが wiki に無い | auto-ingest LaunchAgent のログ確認、`ingest` 手動実行 |
| 議事録が古いまま | `--full --db meetings` で再同期 |
| Daily Log だけ空 | Notion に当日の Daily Log エントリを作成 |

## 正本の関係

| 用途 | 正本 |
|------|------|
| チーム共有・タスク実行 | Notion |
| AI が横断参照するナレッジ | Obsidian wiki（`.raw/` 経由で ingest） |
| プロジェクト進捗の決定 | Git `status.md` |

Notion → Obsidian は **ミラー（コピー）**。矛盾時は用途に応じて上表を参照。
