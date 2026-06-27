# ナレッジ正本マップ（SSoT）

CEO の議論・決定・数値が散らばらないための **唯一の参照表**。
矛盾したら、この表の「正本」列を信頼する。

**詳細アーキテクチャ（Obsidian 正本）:** vault 内 `wiki/meta/knowledge-architecture.md`

## Vault パス

```
/Users/sho_sakakura/Library/Mobile Documents/iCloud~md~obsidian/Documents/claude-obsidian
```

## 正本一覧

| 情報の種類 | 正本（SSoT） | ミラー / ソース | AI が最初に読むもの |
|-----------|-------------|----------------|-------------------|
| 横断コンテキスト | Obsidian `wiki/hot.md` | Notion Snapshot（19:00 ミラー） | `hot.md` |
| 資産・家計・プロフィール | Obsidian `wiki/entities/sakakura-assets.md` 等 | Git `company/memory/` は **ポインタのみ** | Obsidian entity |
| 転職・キャリア | Obsidian `wiki/domains/転職活動.md` | Notion 転職 DB | domain + hot |
| プロジェクト進捗 | Git `company/projects/[id]/status.md` | Obsidian entity は週次要約 | `status.md` |
| タスク・議事録 | Notion DB → `.raw/` | Obsidian `.raw/notion-*` | Notion MCP または `.raw/` |
| 日次統合 packet | Obsidian `wiki/meta/YYYY-MM-DD-daily-knowledge.md` | Notion Daily Log export | meta + hot |
| 日次活動ログ | Obsidian `wiki/log.md` | Notion Daily Log | `log.md` |
| Claude Code 会話 | Obsidian wiki + hot `claude-code:` | Notion export | wiki |
| Cowork 会話 | Obsidian wiki + hot `cowork:` | Notion export | wiki |
| claude.ai 会話 | Obsidian `sources/claude-ai-recents-*` | Notion export | sources |
| Codex 会話 | Obsidian meta/daily-knowledge + hot `codex:` | Notion export | meta |
| Cursor 会話 | Obsidian `wiki/sources/cursor/` + hot `cursor:` | Notion export（Daily Log） | wiki/sources/cursor |

## 3レイヤー運用（2026-06-18 更新）

| レイヤー | ツール | 役割 |
|---------|--------|------|
| **正本** | Obsidian wiki | すべての知識・コンテキスト |
| **ソース** | Gmail, Notion, RSS, Git status | → Obsidian に取り込む |
| **ミラー** | Notion Snapshot, Daily Log DB | Obsidian からエクスポート。AI が vault に触れないときの fallback |

## 同期パイプライン

詳細: Obsidian `wiki/meta/automation-schedule.md`

| ジョブ | 時刻 (JST) | 方向 |
|--------|-----------|------|
| 朝 ingest（Notion fetch, market, intel, …） | 06:30–09:00 | → Obsidian |
| **cursor-daily-sync** | **08:30** | **Cursor agent-transcripts + plans/commits → Obsidian + Notion Daily Log** |
| cowork / claude-ai 取り込み | 17:00 / 18:00 | → Obsidian |
| **sync-wiki-to-notion** | **19:00** | **Obsidian → Notion Snapshot（唯一）** |
| daily-knowledge-packet | 23:20 | sources → Obsidian meta |
| codex-obsidian-daily-memory | 23:30 | Codex → Obsidian meta + hot codex: |

秘密情報: `~/.claude/obsidian-sync.env`

## AI ツール共通ルール

1. セッション開始: `hot.md` → `index.md` → 関連 entity/domain
2. 保存: Obsidian wiki のみ（memory/ はリンクのみ）
3. Notion への書込は automation のエクスポート step のみ

## 週次 wiki 衛生

`wiki-monthly-lint`（月1）+ 金曜 PMO。hot.md Recent Context 20行上限。

## 保存トリガー

資産・決定・「覚えておきたい」→ Obsidian。`company/memory/` 新規は CEO 承認後。
