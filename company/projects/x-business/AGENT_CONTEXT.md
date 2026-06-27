# X事業 — 軽量チャット用コンテキスト

- プロジェクトID: `x-business`
- 最終更新: 2026-05-29
- 詳細: `status.md` / `company/memory/2026-05-17-x-business.md`

---

## 概要

- アカウント: **湾岸ウォッチャー**（@hakushu7）
- 目的: 湾岸エリアの情報発信、反応分析、事業検証
- **文案生成**: Cursor（このチャット）
- **実投稿**: `~/Projects/wangan-agent` → http://localhost:3000/morning.html（朝ブリーフ推奨）

---

## 運用ルール

- 完全自動投稿は **禁止**（候補生成まで）
- 280字以内、具体住所・家族情報・職場は載せない
- APIキーは company-hq に保存しない

---

## 今すぐ（status 要約）

| 優先 | タスク | 期限 |
|------|--------|------|
| 高 | X事業の目的とターゲット市場を定義 | 2026-06-06 |
| 高 | 北極星指標と週次KPIを決める | 2026-06-06 |
| 中 | 投稿カテゴリ・トーン・承認基準を整理 | 2026-05-31 |

---

## wangan-agent 起動

**サイトにアクセスできない** → サーバーが止まっている。下のどちらかで起動:

```bash
# 方法1: company-hq からダブルクリック
open_wangan_agent.command

# 方法2: ターミナル
bash ~/company-hq/tools/wangan_agent/start.sh
```

手動:

```bash
cd ~/Projects/wangan-agent && npm run start:morning
# → http://localhost:3000/morning.html
```

詳細UI（全件管理）: http://localhost:3000/index.html

接続確認のみ: `npm run verify:x`

---

## 新チャットの一行

```
@x-business-light-chat @company/projects/x-business/AGENT_CONTEXT.md を前提に。agent-transcripts は読まないで。
```
