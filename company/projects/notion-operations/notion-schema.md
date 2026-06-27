# Notion DB設計

Notionに「会社HQ」ページを作り、その配下に以下の3つのデータベースを作る。

## 1. 議事録DB

DB名: `議事録`

| プロパティ | 種類 | 用途 |
|------------|------|------|
| 名前 | Title | 会議名 |
| 日付 | Date | 開催日、必要なら時間も入れる |
| 種別 | Select | 定例, 商談, イベント, 経理, 戦略, IT, その他 |
| 関連プロジェクト | Select | bon-odori-harumi-2026, x-business, instagram-business など |
| 参加者 | Multi-select | 参加者名 |
| ステータス | Select | draft, reviewed, done |
| 決定事項 | Text | 決まったことの要約 |
| ToDo | Relation | `タスク` DBへの関連 |
| 次回予定 | Date | 次回会議があれば入れる |

### ページ本文テンプレート

```markdown
## 目的
-

## アジェンダ
-

## 決定事項
-

## 議論メモ
-

## ToDo
- [ ] 

## CEO確認事項
-
```

## 2. タスクDB

DB名: `タスク`

| プロパティ | 種類 | 用途 |
|------------|------|------|
| タスク名 | Title | 動詞で始まるタスク名 |
| 担当 | Select | CEO, COO, 秘書, 経理, 営業, 戦略, IT, Event Ops, PMO |
| 期限 | Date | 期限 |
| ステータス | Select | todo, doing, waiting, done |
| 優先度 | Select | high, medium, low |
| 関連プロジェクト | Select | プロジェクトID |
| 関連議事録 | Relation | `議事録` DBへの関連 |
| メモ | Text | 補足 |

### ビュー

- `今日やる`: 期限が今日以前、ステータスがdone以外
- `今週やる`: 期限が今週、ステータスがdone以外
- `担当別`: 担当でグループ化
- `プロジェクト別`: 関連プロジェクトでグループ化

## 3. 予定DB

DB名: `予定`

| プロパティ | 種類 | 用途 |
|------------|------|------|
| 予定名 | Title | 予定名 |
| 日時 | Date | 日時 |
| 種別 | Select | MTG, 締切, イベント, 支払, 提出, その他 |
| 場所 | Text | URLや会場 |
| 関係者 | Multi-select | 参加者、関係者 |
| 関連プロジェクト | Select | プロジェクトID |
| 準備タスク | Relation | `タスク` DBへの関連 |
| メモ | Text | 補足 |

### ビュー

- `カレンダー`: 日時のカレンダービュー
- `今週`: 今週の予定
- `イベント`: 種別がイベント

## 命名ルール

- 会議名: `YYYY-MM-DD_[テーマ]`
- タスク名: `作成する`, `確認する`, `送る` など動詞で始める
- プロジェクトID: `company/projects/` のフォルダ名に合わせる

## 初期プロジェクト候補

- `bon-odori-harumi-2026`
- `x-business`
- `instagram-business`
- `notion-operations`

## 4. 動画メモDB

DB名: `動画メモ`

| プロパティ | 種類 | 用途 |
|------------|------|------|
| タイトル | Title | 動画タイトル |
| URL | URL | YouTube URL |
| 視聴日 | Date | 視聴日 |
| チャンネル | Text | チャンネル名 |
| 要約 | Text | 3行要約 |
| タグ | Multi-select | トピックタグ |
| 関連プロジェクト | Select | bon-odori-harumi-2026, wangan, minpaku など |
| ステータス | Select | queued, processing, done, failed |

### ビュー

- `最近`: 視聴日の新しい順
- `プロジェクト別`: 関連プロジェクトでグループ化
- `要確認`: ステータス failed またはタグ unprocessed

### 連携

- ローカル処理: `tools/video_knowledge/process_video.py --notion`
- 拡張連携: `tools/video_knowledge/server.py` + `apps/video-capture-extension/`
- ローカルMarkdown: `company/memory/videos/`
