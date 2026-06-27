# プロジェクト台帳

このディレクトリは、進行中の事業・案件をCOO/PMOが管理するための場所です。

## 使い分け

- `company/memory/`: 決定事項、事業方針、継続参照する知識
- `company/projects/`: 実行中プロジェクトの進捗、タスク、担当、期限

## Single Source of Truth（SSoT）

| ファイル | 役割 |
|---------|------|
| `company/projects/[id]/status.md` | **正**。決定・タスク・未決・リスクは常にここを更新 |
| `company/projects/[id]/AGENT_CONTEXT.md` | status の要約（200行以内）。週1または大きな決定時に同期 |
| `company/projects/_portfolio/status.md` | 全案件の週次集約（PMOが各 status から更新） |
| `company/projects/registry.yaml` | 機械可読な案件台帳 |

**矛盾時は `status.md` を優先**する。`AGENT_CONTEXT.md` と portfolio は status に追随する。

## 標準構成

新規案件は [\_template/](_template/) をコピーして開始する。

```text
company/projects/[project-id]/
├── status.md           # 現状、次アクション、リスク（必須）
├── AGENT_CONTEXT.md    # 軽量チャット用要約（推奨）
├── schedule.md         # マイルストーン（任意）
├── comms.md            # チーム共有文・外部連絡文（任意）
├── tasks.md            # 詳細タスク（任意）
└── finance.md          # 予算、見積、売上、経費（任意）
```

## ステータス定義

| 状態 | 意味 |
|------|------|
| `planning` | 企画・前提整理中 |
| `active` | 実行中 |
| `waiting` | 外部返答・日程待ち |
| `blocked` | CEO判断または外部要因で停止 |
| `done` | 完了 |

## COO運用

1. 新しい事業・案件が出たら `project-id` を付け、`registry.yaml` に登録
2. `status.md` に現状と次アクションを集約する
3. 継続作業が多い案件は `AGENT_CONTEXT.md` と `@*-light-chat` ルールを追加
4. 週次で `active` / `waiting` / `blocked` を見直す
5. 確定した重要事項は `company/memory/` への保存をCEOに提案する

## 現在の管理プロジェクト

| project-id | 概要 | 軽量チャット |
|------------|------|-------------|
| `bon-odori-harumi-2026` | 盆踊り・出店運営 | `@bon-odori-light-chat` |
| `x-business` | X・湾岸ウォッチャー | `@x-business-light-chat` |
| `instagram-business` | Instagram | `@instagram-light-chat` |
| `notion-operations` | Notion議事録・予定・タスク | `@notion-ops-light-chat` |
| `video-knowledge` | 動画文字起こし | `@video-knowledge-light-chat` |

その他: [docs/agent-routing.md](../../docs/agent-routing.md)（秘書・沖縄民泊・湾岸DB等）

## 関連ドキュメント

- チャット運用: [docs/agent-playbook.md](../../docs/agent-playbook.md)
- **話題別早見表**: [docs/agent-routing.md](../../docs/agent-routing.md)
- 案件台帳: [registry.yaml](registry.yaml)
