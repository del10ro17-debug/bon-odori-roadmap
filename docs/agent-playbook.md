# Agent チャット運用プレイブック

CEO が Cursor Agent を効率よく使うためのガイド。

## 4つのルーティングモード

| モード | いつ使う | 起動例 |
|--------|---------|--------|
| **Executive** | 方針・複数部門・CEO確認 | （デフォルト）「COO、来週の予定を整理して」 |
| **Direct** | コード実装・単一スキル | `@it このバグを直して` |
| **Project** | 1案件の継続作業 | `@bon-odori-light-chat @.../AGENT_CONTEXT.md` |
| **Portfolio** | 週次優先順位 | `@pmo ポートフォリオ更新` |

## 新チャットを開く判断基準

| 状況 | 推奨 |
|------|------|
| コンテキストが70%超 | **新チャット** + 該当 `AGENT_CONTEXT.md` |
| UI大改修とデータ更新が混在 | **別チャットに分離**（盆踊りWebで実証済み） |
| 全く別の事業・案件 | 新チャット（スキル明示 or Project mode） |
| 単純な1ファイル修正 | 同チャット or Direct `@it` |

## Project mode（軽量チャット）の使い方

1. 新規 Agent チャットを開く
2. 最初の一行に `@*-light-chat` と `AGENT_CONTEXT.md` を指定
3. エージェントは status の要約だけ読み、transcript は読まない

### 利用可能な light-chat ルール

話題別の一覧・コピペ用一行は **[agent-routing.md](agent-routing.md)** を参照。

| ルール | 対象 |
|--------|------|
| `@bon-odori-light-chat` | 盆踊り2026出店 |
| `@x-business-light-chat` | X投稿・湾岸ウォッチャー文案 |
| `@instagram-light-chat` | Instagram・湾岸暮らしメモ |
| `@secretary-light-chat` | 日程・議事録・メール下書き |
| `@notion-ops-light-chat` | Notion運用 |
| `@wangan-price-light-chat` | 湾岸価格DB・不動産評価 |
| `@okinawa-minpaku-light-chat` | 沖縄民泊・物件精査 |
| `@video-knowledge-light-chat` | 動画文字起こし |
| `@wangan-family-light-chat` | 湾岸ファミリーアプリ |
| `@maruke-light-chat` | まるつけ（宿題丸つけ・公庫・採点精度） |

## 情報の正（SSoT）

```
status.md（正） → AGENT_CONTEXT.md（要約） → _portfolio/status.md（週次集約）
```

矛盾したら **status.md を信頼**する。

## Direct mode の例

```
@it docs/wangan-price-dashboard/data.js のバグを直して
@video-knowledge この動画を文字起こしして /path/to/video.mp4
@wangan-real-estate 晴海フラッグ SEA VILLAGE 1205 の時価を出して
```

COO の【COO】見出し・長い振り分け説明は省略される。

## 週次 PMO ルーティン

1. `@pmo ポートフォリオ更新`
2. 各 `company/projects/*/status.md` と `_portfolio/status.md` の整合確認
3. 今週の最優先5件以内に絞る
4. `registry.yaml` の status が古ければ更新

## Git vs Notion vs Obsidian

| 保存先 | 用途 |
|--------|------|
| **Obsidian wiki** | 横断ナレッジ、hot cache、資産・転職・学び（**draft 正本**） |
| **Git** | プロジェクト `status.md`、スキル、AGENT_CONTEXT、設計、コード |
| **Notion** | 議事録、タスク、予定、Daily Log（**published 正本**） |

正本マップ: [knowledge-ssot.md](knowledge-ssot.md)

議事録を Notion に保存する前のチェック: [secretary-workflow.md](../company/projects/notion-operations/secretary-workflow.md)

## 週次 wiki 衛生

`@pmo` 週次レビューに含める（金曜推奨）:

1. Obsidian lint（矛盾・古い日付）
2. `wiki/hot.md` を50行以内に圧縮
3. 各 `status.md` → Obsidian entity に1段落反映
4. `wiki/questions/` に今週の重要 Q&A を1件
5. 同期ログ確認: `/tmp/notion-daily-fetch.log`, `/tmp/cursor-daily-sync.log`

セットアップ: [tools/knowledge_sync/README.md](../tools/knowledge_sync/README.md)

## パフォーマンス

- `.cursorignore` で `node_modules/`, `.venv/`, 大きな DB/PDF を除外
- alwaysApply ルールは `coo-orchestrator` + `approval-policy` の2つのみ維持
- プロジェクト作業は glob rule（light-chat）で必要な文脈だけ注入

## 関連

- [AGENTS.md](../AGENTS.md) — 組織・3層・スキル一覧
- [company/projects/README.md](../company/projects/README.md) — プロジェクト台帳
- [company/handbook.md](../company/handbook.md) — 会社方針・優先順位
