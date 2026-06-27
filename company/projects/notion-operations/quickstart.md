# Notion運用クイックスタート

## 1. Notionページを作る

Notionで `会社HQ` というページを作る。

ページ本文には `notion-page-template.md` の内容を貼る。

## 2. DBを3つ作る

`会社HQ` の中に以下を作る。

- `議事録`
- `タスク`
- `予定`

プロパティは `notion-schema.md` に合わせる。

## 3. 初期データを入れる

必要なら以下のCSVをNotionにインポートする。

- `import-meetings.csv`
- `import-tasks.csv`
- `import-schedule.csv`

NotionのCSVインポート後、プロパティ型を調整する。

- 日付系: Date
- 種別、担当、ステータス、優先度、関連プロジェクト: SelectまたはMulti-select
- メモ、決定事項: Text

## 4. 最初のテスト

COOにこう依頼する。

```text
COO、Notion運用のテストをします。週次優先順位MTGの議事録本文と、タスクDBに入れる行を作って。
```

期待する出力:

- `議事録` のページ本文
- `タスク` に追加する項目
- `予定` に追加する項目
- CEO確認事項

## 5. CursorのNotion MCP接続

このプロジェクトには `.cursor/mcp.json` を追加済み。

```json
{
  "mcpServers": {
    "notion": {
      "url": "https://mcp.notion.com/mcp"
    }
  }
}
```

次にCursor側で行うこと:

1. Cursorを再読み込みする。
2. Cursor Settings → MCP を開く。
3. `notion` が表示されていることを確認する。
4. 認証を求められたらNotion OAuthを完了する。
5. 権限はできるだけ `会社HQ` ページに限定する。
