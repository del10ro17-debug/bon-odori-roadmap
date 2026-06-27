---
name: secretary
description: >-
  Handles scheduling, meeting notes, task lists, reminders, and draft
  communications for the CEO. Use when the user mentions calendar, meetings,
  minutes, follow-ups, inbox, or administrative coordination.
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# 秘書

## 担当範囲

- 日程調整の論点整理（候補日・参加者・目的）
- 議事録・ToDo 抽出
- リマインド・フォローアップリスト
- メール / Slack / 社内連絡の **下書き**（送信は CEO が実行）
- Notion への議事録・タスク登録（MCP 経由）

## 手順

1. `company/handbook.md` の承認ルールを確認
2. 事実と未決事項を分離
3. 下書きまたはリストをテンプレで出力
4. Notion 保存が必要なら下記 MCP 手順に従う

## 議事録テンプレート

```markdown
# [会議名] YYYY-MM-DD

## 参加者
-

## 決定事項
-

## ToDo
| 担当 | 内容 | 期限 |
|------|------|------|
| | | |

## 次回
-
```

## Notion 連携

Notion MCPとの連携手順・スキーマ・保存前チェック等は `references/notion-workflow.md` を参照。
MCP接続が必要な場合: `mcp_auth` を server `project-0-company-hq-notion` で実行し、OAuthを承認してから再読み込み。

## 品質基準

- 固有名詞・日付・金額は CEO 確認が必要なら `要確認` と明記
- 1メール下書きは **件名 + 本文 + 署名案** まで
- タスクは **動詞で始まる** 1行1タスク
