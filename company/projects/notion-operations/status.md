# Notion Operations

- 状態: `active`
- 主管: COO / PMO
- 関連部門: 秘書, IT
- 目的: スケジュール、議事録、ToDoをNotionで一元管理する
- 最終更新: 2026-05-29（再実行）

## Notion リンク（会社HQ）

| リソース | URL |
|---------|-----|
| 会社HQ | https://www.notion.so/3633d2ab617d81af81f3e2c548bcfbb2 |
| 議事録 DB | https://www.notion.so/a755adb2c9584da08c3cd009f95bf56a |
| タスク DB | https://www.notion.so/854bb7ac1e7447588275960c4601f11e |
| 予定 DB | https://www.notion.so/5534fbf1a2ec4e41b1712f775e425b50 |

## 現状

- 会社HQ ページ配下に **議事録・タスク・予定** の3 DB が利用可能。
- 2026-05-29: Notion MCP 認証成功。接続テスト完了。
- 議事録 DB を新規作成（`notion-schema.md` 準拠）。タスク DB との双方向 Relation 設定済み。
- 予定 DB に「準備タスク」Relation を追加済み。
- MCP テスト議事録（初回）: [2026-05-29_Notion MCP接続テスト](https://www.notion.so/36e3d2ab617d81c49ccbeeeee497b7a5)
- MCP テスト議事録（PMO）: [2026-05-29_週次PMOポートフォリオレビュー](https://www.notion.so/36e3d2ab617d81d98bd6c49b82839ffd)
- 週次 PMO 予定: [週次 PMO ポートフォリオレビュー](https://www.notion.so/36e3d2ab617d81e9b37afe56fbd780de)（毎週金曜 9:00 想定）
- 最優先5件を Notion タスク DB に同期済み（2026-05-29 再実行）

## 完了済み

- [x] 会社HQ ページ作成
- [x] タスク DB 作成（スキーマ準拠）
- [x] 予定 DB 作成（スキーマ準拠 + 準備タスク Relation）
- [x] 議事録 DB 作成（スキーマ準拠 + ToDo Relation）
- [x] Notion MCP OAuth 認証
- [x] MCP 接続テスト（議事録1件 + タスク1件 + 予定1件）

## Notion → Obsidian 同期

- スクリプト: Obsidian `scripts/notion-company-sync.js`
- 手順: [tools/knowledge_sync/notion-to-obsidian-setup.md](../../tools/knowledge_sync/notion-to-obsidian-setup.md)
- **ブロッカー（2026-06-18）**: API 連携 `claude-obsidian` がアクセスできるのは Daily Log のみ。議事録・タスク・予定 DB を Connections で共有後、`--full` で初回移行。

```bash
bash tools/knowledge_sync/run-notion-company-sync.sh --full
```

## 今週やること

| 優先 | 担当 | タスク | 期限 | 状態 |
|------|------|--------|------|------|
| 高 | CEO | 会社HQ 配下 DB を claude-obsidian 連携に共有 | 2026-06-20 | **要対応** |
| 高 | IT | 共有後 `--full` で Obsidian 初回移行 + LaunchAgent 登録 | 共有後 | ready |
| 中 | PMO | 各プロジェクトの高優先タスクをNotionタスクDBに同期 | 2026-06-06 | done |
| 低 | IT | 動画メモ DB を追加（`notion-schema.md` §4） | 未設定 | backlog |

## CEO確認事項

- 週次レビュー日を固定するか（現状: 金曜 9:00 想定で予定登録済み）

## リスク

- Notion権限が広すぎると不要なページまで見える可能性がある。
- スケジュールはGoogle Calendar等と二重管理になりやすいため、当面は「準備タスクと会議記録」を中心に使う。

## 関連

- 秘書運用: [secretary-workflow.md](secretary-workflow.md)
- 軽量チャット: `@notion-ops-light-chat`
- Agent playbook: [docs/agent-playbook.md](../../docs/agent-playbook.md)
