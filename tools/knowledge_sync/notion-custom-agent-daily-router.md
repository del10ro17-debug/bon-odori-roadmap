# Notion Custom Agent — Daily Knowledge Router

選考パイプライン DB と日次 Notion 情報の自動振り分け。

## 選考パイプライン DB

| 項目 | 値 |
|------|-----|
| URL | https://app.notion.com/p/a3ff6d2f060c4d589aeb8d5cc0661317 |
| 配置 | Claude Context Hub 配下 |
| data_source_id | `ec099d75-510d-406e-b7e8-73d442524792` |
| 初期行 | 7社（2026-06-18 seed） |

### Obsidian 同期

`claude-obsidian` 連携に **Connections で共有**後:

```bash
bash tools/knowledge_sync/run-notion-company-sync.sh --db career-pipeline
```

出力: `.raw/notion-career-pipeline-{date}-{slug}-{id8}.md`

---

## Custom Agent 作成手順（Enterprise）

Notion → **Settings** → **Agents** → **New agent**

### 基本設定

| 項目 | 値 |
|------|-----|
| Name | `Daily Knowledge Router` |
| Description | 日次 Notion 情報を構造化 DB へ振り分ける |

### アクセス権

**Read**

- `📅 Daily Claude Log`
- `Claude Context Hub`（朝ブリーフ、Daily Knowledge Log、面接関連ページ）

**Write**

- `選考パイプライン`
- `💬 Conversation DB`
- `🎯 転職ナレッジDB`
- 会社HQ → `タスク` / `予定`

### トリガー

- **Schedule:** 毎日 21:30 JST（初回はこれだけで十分）

### Instructions（コピペ）

```
あなたは坂倉翔の Notion ワークスペース用ナレッジルーターです。
毎回、直近48時間以内に更新されたページだけを対象に、構造化DBへ振り分けます。

## 読むソース（優先順）
1. Daily Claude Log（Tags=転職活動, 朝ブリーフ, cursor-sync）
2. タイトルに「朝ブリーフ」「Daily Knowledge Log」が含まれるページ
3. タイトルに「面接」「Interview」「GTM」が含まれる転職関連ページ

## 振り分けルール

### → 選考パイプライン DB
- 企業名・ステージ変更・次アクション・優先度が書かれているとき
- 既存行があれば更新、なければ新規作成
- ステージ: リサーチ/スカウト/1次/2次/プレゼン/オファー/辞退/終了
- 必ず「ソース」に元ページURL、「最終更新」に今日の日付

### → Conversation DB
- 1回の面接・通話・メールスレッド = 1行
- カテゴリ=転職面談
- 要点サマリー（3行以内）、アクションアイテム、ソースURL

### → 転職ナレッジDB
- 再利用できる回答・フレーム・企業研究メモのみ
- Type=選考ログ / 学び / 企業研究 / 条件/判断基準
- Status=Draft

### → 会社HQ タスク
- 期限または「〜までに」が明記された Next Action のみ
- タスク名は動詞で始める

### → 会社HQ 予定
- 面接日時・締切が具体的な日時のときのみ

## やらないこと
- 面接プレゼン・ビジネスプラン全文のコピー
- Daily Log / 朝ブリーフ本体の上書き
- 01 転職活動ダッシュボードの古い表の編集
- CADDi 社内MTG
- 推測でのステージ更新（ソースに根拠がない変更はしない）

## 完了報告
- 処理したソースページ数
- 各DBへの create / update 件数
- スキップした理由
```

### 初回テスト

1. Agent 画面で **Run now**
2. 選考パイプラインに不要な重複行がないか確認
3. 問題なければ 21:30 スケジュールを有効化

---

## CEO 確認（1回）

- [ ] 選考パイプライン DB を `claude-obsidian` Connections に追加
- [ ] Custom Agent を作成し Run now でテスト
- [ ] `run-notion-company-sync.sh --db career-pipeline` で Obsidian 反映確認
