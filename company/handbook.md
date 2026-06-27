# 会社ハンドブック

## 基本情報

- **社名**: 坂倉HQ（仮想会社 / company-hq リポジトリ）
- **ミッション**: CEO の複数事業・案件を1つのHQで効率よく実行する
- **主要顧客 / 市場**: CEO本人の事業（湾岸不動産、イベント出店、沖縄民泊、地域メディア、EdTech等）
- **会計年度 / 通貨**: 4月始まり / JPY

## 方針

### 優先事業ランキング（2026-06 時点）

> **ライブ版**: 週次の正は `_portfolio/status.md` + Obsidian `wiki/hot.md`。本表は月次の方針メモ。

1. **盆踊り2026出店** — 本番 7/11–12。**期限固定のため最優先**
2. **まるつけ（maruke-app）** — 公庫融資・実採点精度・P0完成（active）
3. **転職活動** — CEO 横断スレッド（Obsidian `wiki/domains/転職活動.md`）。HQ外だが時間配分に影響
4. **湾岸不動産** — 価格DB・保有資産評価
5. **沖縄民泊** — 物件精査・融資準備（planning）
6. **Notion / 動画ナレッジ** — HQ基盤整備
7. **X / Instagram / 湾岸ファミリーアプリ** — planning 段階

### 優先すること

- 期限のある案件（イベント本番等）を他より先に処理する
- 決定事項は `status.md` に集約し、エージェント間で矛盾を出さない
- 外部送信・本番変更は CEO 承認後
- ポートフォリオは週次（本番直前案件は週2回）で `_portfolio/status.md` を更新する

### やらないこと

- SNS の完全自動投稿（候補生成まで。投稿は人間レビュー後）
- 個人情報・認証情報の外部送信・リポジトリ保存
- 税務・法務・宅建の断定（専門家確認を促す）
- agent-transcripts の読取（プロジェクト軽量チャット時）

## 用語・略語

| 用語 | 意味 |
|------|------|
| CEO | 坂倉 翔（ユーザー） |
| COO | Cursor Agent のデフォルト窓口 |
| 湾岸 | 豊洲・晴海・勝どき・月島・有明・東雲エリア |
| HARUMI FLAG | 晴海フラッグ街区 |
| SSoT | Single Source of Truth — 種類ごとの正本。詳細 [docs/knowledge-ssot.md](../docs/knowledge-ssot.md) |
| Obsidian wiki | 横断ナレッジの正本。Vault は CLAUDE.md 参照 |
| 話題別エージェント | [docs/agent-routing.md](../docs/agent-routing.md) — どのチャットに何を頼むか |

## 連絡・承認

- **CEO**: 坂倉 翔
- **承認が必要なこと**: 契約、大きな支出、対外公開、`git push`、本番デプロイ、`company/memory/` への新規決定ログ
- **詳細**: `.cursor/rules/approval-policy.mdc` を参照
