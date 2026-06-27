Notion MCP で会社HQ・AIミーティングノートを Obsidian .raw/ に一括エクスポートして。

Vault: /Users/sho_sakakura/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian
出力先: .raw/

## 1. 会社HQ DB（SQL query → fetch → Write）

| DB | collection URL |
|----|----------------|
| 議事録 | collection://af0d3bee-141d-4844-bdb1-b23ef1962cde |
| キャディ 議事録 | collection://49a4b49e-3171-476d-be7d-b7bfcc647963 |
| プライベート議事録 | collection://1a43bff8-3799-4577-92af-02d4e9e0b116 |
| タスク | collection://77c7d90c-781d-45eb-abf2-4cb649d4ef85 |
| 予定 | collection://f78782ee-d4d6-4bc8-8c39-6c059e94f9dc |

- 議事録系: 1ページ1ファイル `notion-meeting-{date}-{slug}-{id8}.md`
- タスク/予定: 日次スナップショット `notion-tasks-{today}.md`, `notion-schedule-{today}.md`

frontmatter 必須:
```
---
source: Notion
database: {DB名}
notion_url: {url}
date: {YYYY-MM-DD}
synced_at: {ISO8601}
---
```

## 2. AI ミーティングノート（notion-query-meeting-notes）

過去1年分を月ごとに query（created_time filter）し、各ページを notion-fetch（include_transcript: true）で取得。

ファイル名: `notion-ai-meeting-{date}-{slug}-{id8}.md`

## 3. 完了報告

- 書き出したファイル数（DB別）
- スキップ/エラー
- `.raw/.notion-mcp-export-{today}.json` にエクスポート一覧を保存
