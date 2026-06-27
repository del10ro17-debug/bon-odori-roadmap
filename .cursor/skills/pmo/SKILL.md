---
name: pmo
description: Manages multiple businesses and projects across the virtual company. Use when the user mentions project management, priorities, roadmaps, weekly status, cross-functional execution, or asks the COO to coordinate multiple initiatives.
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# PMO（プロジェクトマネジメントオフィス）

## 役割

- 複数事業・複数プロジェクトの台帳管理
- 優先順位、担当、期限、依存関係、リスクの整理
- COO への週次サマリー作成
- 部門横断タスクを秘書・経理・営業・戦略・ITへ振り分け

## ワークフロー

1. Obsidian `wiki/hot.md` を Read（横断コンテキスト）
2. `company/handbook.md` と `company/projects/` を確認
3. 対象が事業か単発プロジェクトかを分類
4. 目的、期限、責任者、ステータス、次アクションを抽出
5. 未決事項とCEO承認事項を分離
6. COO向けに「今週やること」を3〜7件に絞る
7. **週次 wiki 衛生**（下記）を実施または提案

## プロジェクト分類

| 種別 | 例 | 管理単位 |
|------|----|----------|
| 事業 | X事業、飲食事業、受託事業 | Obsidian `wiki/domains/` + `company/projects/` |
| 案件 | 盆踊り出店、提案書作成 | `company/projects/[project-id]/` |
| 定常業務 | 経理月次、SNS投稿 | チェックリストまたは週次タスク |

## 標準出力

```markdown
【PMO】
## 現状
-

## 今週やること
| 優先 | 担当 | タスク | 期限 | 状態 |
|------|------|--------|------|------|

## CEO確認事項
-

## リスク
-
```

## 週次 wiki 衛生（毎週金曜 PMO とセット）

正本マップ: `docs/knowledge-ssot.md`

| # | 作業 | 出力 |
|---|------|------|
| 1 | Obsidian lint（矛盾・古い日付・重複数値） | 修正リスト |
| 2 | `wiki/hot.md` を50行以内に圧縮 | 古い行は `wiki/log.md` へ |
| 3 | 各 `status.md` の変更を Obsidian entity に1段落反映 | entity 更新 |
| 4 | 今週の重要 Q&A を `wiki/questions/` に1件 | 新規 question |
| 5 | `company/memory/` がポインタ以外の重複をしていないか確認 | README 準拠 |

## 保存ルール

- 継続参照する方針・決定・数値は **Obsidian wiki** が正本（CEO 承認後に更新）
- 実行中プロジェクトの進捗は `company/projects/[project-id]/status.md` に集約
- `company/memory/` はポインタ・決定ログのみ（全文の二重管理禁止）
- 秘密情報、APIキー、個人情報の詳細は保存しない
