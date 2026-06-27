# Notion 連携ワークフロー — 秘書

## 前提

- MCP 設定: `.cursor/mcp.json`（公式 Notion MCP `https://mcp.notion.com/mcp`）
- DB 設計: `company/projects/notion-operations/notion-schema.md`
- 運用フロー例: `company/projects/notion-operations/secretary-workflow.md`
- プロジェクト状態: `company/projects/notion-operations/status.md`

## MCP 接続

1. Notion MCP ツールが使えない場合、`mcp_auth` を server `project-0-company-hq-notion` で実行（CEO が OAuth 承認）
2. チャットを再読み込みしてから Notion ツールを呼ぶ
3. 認証情報・APIキーはリポジトリに保存しない

## 議事録を Notion に保存する手順

1. チャットで議事録ドラフトを作成（上記テンプレ）
2. `notion-schema.md` の「議事録DB」プロパティに合わせて整形:
   - 名前（Title）、日付、種別、関連プロジェクト、参加者、ステータス、決定事項
3. Notion MCP でページ作成（DB: `議事録`）
4. ToDo があれば「タスクDB」にも登録（Relation で議事録とリンク）
5. 保存前チェック（下表）

## Notion 保存前チェック

| チェック | 内容 |
|----------|------|
| 秘密情報 | APIキー、パスワード、口座情報が含まれていない |
| 個人情報 | 必要以上の個人情報がない |
| 決定事項 | CEO が確定した内容だけ |
| ToDo | 担当と期限がある。未定なら `要確認` |
| 関連 | プロジェクトID（`bon-odori-harumi-2026` 等）が入っている |

## Git vs Notion

| 保存先 | 用途 |
|--------|------|
| Git `status.md` | プロジェクトの正（決定・タスク・未決） |
| Notion | 議事録全文、実行タスク、予定 |

Git の `status.md` と Notion タスクが矛盾した場合、**Git を正**とし、Notion を追随させる。
