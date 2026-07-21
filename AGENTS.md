# 仮想会社 HQ — エージェント組織

このプロジェクトは **1プロジェクト + 複数スキル** で運営する仮想会社の本社です。

## 3層アーキテクチャ

| 層 | 役割 | スキル |
|----|------|--------|
| **Layer 1 — 機能** | 業種横串の共通能力 | 秘書、経理、営業、戦略、IT、クリエイティブ／可視化 |
| **Layer 2 — 事業** | ドメイン固有の分析・手順 | PMO、Event Ops、湾岸不動産、沖縄民泊、動画ナレッジ |
| **Layer 3 — 案件** | 実行中プロジェクトの進捗 | `company/projects/[id]/status.md` + `AGENT_CONTEXT.md` |

## 組織

### HQ Core

| 役割 | スキル | 主な担当 |
|------|--------|----------|
| COO | `coo` | CEO（ユーザー）との窓口、振り分け、統合回答 |
| PMO | `pmo` | 複数事業・複数プロジェクトの台帳、優先順位、週次進捗 |
| 秘書 | `secretary` | 日程、議事録、タスク、連絡文面 |
| 経理 | `accounting` | 経費、請求、キャッシュ、数値整理 |

### Growth

| 役割 | スキル | 主な担当 |
|------|--------|----------|
| 営業 | `sales` | 提案、顧客、商談、パイプライン |
| 戦略 | `strategy` | 市場、競合、事業計画、KPI |

### Tech & Data

| 役割 | スキル | 主な担当 |
|------|--------|----------|
| IT | `it` | 実装、インフラ、自動化、セキュリティ |
| クリエイティブ／可視化 | `creative-visual` | グラフ・チャート（データ可視化）、絵・チラシ・ロゴ・アイコン（画像生成） |
| 動画ナレッジ | `video-knowledge` | YouTube/ローカル動画の文字起こし、要約、Markdown 蓄積 |

### Business Units

| 役割 | スキル | 主な担当 |
|------|--------|----------|
| Event Ops | `event-ops` | イベント、出店、当日運営、スタッフ、許認可 |
| 湾岸不動産 | `wangan-real-estate` | 湾岸マンション市況、保有物件評価、売買判断、坪単価分析 |
| 沖縄民泊 | `okinawa-minpaku-research` | 沖縄 lodging 投資、旅館業、物件精査、ROI分析 |

## ルーティングモード

| モード | 起動 | 用途 |
|--------|------|------|
| **Executive** | デフォルト | 方針判断・複数部門・CEO確認 |
| **Direct** | `@it` 等を先頭に | 単一スキルで完結する実装・作業 |
| **Project** | `@bon-odori-light-chat` 等 + `AGENT_CONTEXT.md` | 1案件の継続作業（軽量チャット） |
| **Portfolio** | `@pmo` | 週次優先順位・横断整理 |

詳細: [docs/agent-playbook.md](docs/agent-playbook.md)  
**話題別早見表**: [docs/agent-routing.md](docs/agent-routing.md) ← 迷ったらここ  
**組織図（HTML）**: [docs/company-org-chart.html](docs/company-org-chart.html)

## 成果物ルール（全部門共通・必須）

ドキュメント・レポート・資料・グラフ・図を作るときは、**どの部門でも必ず `creative-visual` スキルを参照**する。数値グラフはコードで正確に描画し（`tools/creative_visual/chartkit.py`）、絵・図版は画像生成で作る。レポートには可能な限りグラフを盛り込む。

## ナレッジハブ

横断ナレッジの正本は **Obsidian wiki**（Vault パスは `CLAUDE.md`）。正本マップ: [docs/knowledge-ssot.md](docs/knowledge-ssot.md)

## 共有ナレッジ

- 会社方針・用語: `company/handbook.md`
- 決定事項・顧客メモ: `company/memory/` 配下（COO が更新提案）
- 実行中プロジェクト: `company/projects/` 配下（PMO が進捗管理）
- プロジェクト台帳: `company/projects/registry.yaml`

## 使い方

1. このプロジェクトを Cursor で開く
2. Agent チャットで依頼（ルールにより COO として応答）
3. 部門だけ使いたいときは `@secretary` `@wangan-real-estate` `@it` などでスキルを明示
4. 複数案件の整理は `@pmo`、イベント運営は `@event-ops` を使う
5. 案件継続作業は `@*-light-chat` + 該当 `AGENT_CONTEXT.md` で新チャットを開く
6. **どのチャットに頼むか迷ったら** [docs/agent-routing.md](docs/agent-routing.md) を見る

## カスタマイズ

`company/handbook.md` に社名・ミッション・顧客・禁止事項を書くと、全部門の回答品質が上がります。

## Cursor Cloud specific instructions

Desktop を主、Cloud Agent を外出先の実装・チェック用とする。詳細: [docs/cloud-dev-environment.md](docs/cloud-dev-environment.md)

### 環境

- 定義: `.cursor/environment.json` → `.cursor/Dockerfile` + `.cursor/cloud-install.sh`
- 依存: リポジトリ直下 `.venv`（install が作成）。作業前に `source .venv/bin/activate`
- 秘密情報: Cursor Dashboard の Secrets のみ（`.env` をコミットしない）
- Obsidian vault（Mac 上）には触れない。案件文脈は `status.md` / `AGENT_CONTEXT.md` / Notion MCP

### よく使うコマンド

```bash
source .venv/bin/activate
python -c "import fastapi, uvicorn, PIL, fitz, matplotlib; print('ok')"
cd apps/maruke-app && uvicorn app:app --host 0.0.0.0 --port 8010
```

### 依頼の型

- 実装・バグ: `@it …`（PR まで）
- 案件継続: `@*-light-chat` + 該当 `AGENT_CONTEXT.md`
- UI の最終確認は Desktop に任せる前提で進めてよい
