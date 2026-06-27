# Cowork Gmail MCP → Obsidian wiki 取り込み

**前提:** Cowork（Claude Desktop）で Gmail MCP が接続済み。Cursor からは Gmail MCP を使えない。

## なぜ Obsidian に自動で入らないか

Gmail MCP でメールを**読む**だけでは wiki は更新されない。Cowork は Notion へ書くことは多いが、Obsidian への**明示的な Write** が無いと `.raw/` も `転職活動.md` も古いまま。

## 毎回 Cowork に貼るプロンプト（転職・Notion）

```
Gmail MCP で転職関連メールを取り込んで Obsidian wiki を更新して。

1. search_threads:
   query = "from:makenotion.com OR from:ashbyhq.com OR label:転職活動 newer_than:30d"
   pageSize = 20

2. Notion / 面接 / 次ステップ系スレッドは get_thread で全文取得

3. 新規または更新があるメールごとに Write:
   /Users/sho_sakakura/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian/.raw/email-{sender}-{date}.md
   frontmatter: source=Gmail, category=転職活動, date, from, subject

4. Read してから Edit:
   wiki/domains/転職活動.md — Current Status 表・Timeline・Next Action をメール内容で更新

5. wiki/log.md に1行追記（ingest | Gmail Notion ...）

6. wiki/hot.md の直近エントリに1行（YYYY-MM-DD claude: Notion転職メール反映 — 要点30字）

7. 完了報告: 見つかった件名・転職活動.md で変えた行・作成した .raw ファイル名
```

## セッション終了ルール

Cowork で Gmail を見たら、**同セッション内**で上記 3〜6 までやってから終了する。Notion DB だけ更新して wiki をスキップしない。

## OAuth スクリプトとの関係

`sync_career_gmail.py` は Cowork が使えない Cursor / LaunchAgent 用の**予備**。.primary はこの Cowork Gmail MCP フロー。
