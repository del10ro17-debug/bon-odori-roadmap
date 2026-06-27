# X事業 統合メモ

> **履歴スナップショット（2026-05-17）。** 最新方針は Git `company/projects/x-business/status.md` と Obsidian wiki。`company/memory/README.md` 参照。
- 日付: 2026-05-17
- 決定者: CEO
- 内容: X（旧Twitter）を使った投稿生成・投稿運用・メトリクス収集を「X事業」として company-hq に統合する。

## 位置づけ

X事業は、X上での投稿運用を通じてテーマ別の情報発信、反応分析、将来的な事業検証につなげる取り組み。

現時点では「湾岸ウォッチャー」を中心に、AIによる投稿候補生成、人間レビュー、X投稿、投稿後メトリクス収集までを運用対象とする。

## 既存資産

### wangan-agent

- 場所: `~/Projects/wangan-agent`
- 役割: X事業のメイン運用ツール
- 機能:
  - Claude API による投稿候補生成
  - ブラウザUIでの確認・編集・承認
  - X API v2 での即時投稿
  - SQLite `data.db` への投稿履歴保存
  - 投稿後メトリクス収集
- 起動:

```bash
cd ~/Projects/wangan-agent
npm start
```

- 接続確認:

```bash
cd ~/Projects/wangan-agent
npm run verify:x
```

### x-poster

- 場所: `~/Projects/x-poster`
- 役割: テキストをXへ投稿するシンプルなCLI
- 用途: wangan-agent より軽い単発投稿、ファイルベース投稿

### x-auto-post-agent

- 場所: `~/Projects/x-auto-post-agent`
- 役割: 定型文の単発投稿・cron定期投稿
- 備考: 既存の `x-poster` と役割が近いため、当面は補助的な扱い。

## 直近の修正状況

`wangan-agent` の投稿エラー対応として以下を修正済み。

- X API クライアントを `lib/xClient.js` に共通化
- `api.x.com` に接続できない場合、`api.twitter.com` にフォールバック
- `npm run verify:x` で投稿せず認証・接続確認できるようにした
- 投稿前に280文字超過をチェック
- `non_public_metrics` 要求をやめ、403を避けるため `public_metrics` 中心に変更
- 402 / 401 / 403 / 429 / ネットワークエラーの日本語表示を改善

## 運用方針

- Xへの実投稿は原則、人間レビュー・承認後に行う。
- 自動生成は投稿候補の作成までとし、完全自動投稿は当面避ける。
- `.env` のX APIキー、Anthropic APIキー、SQLite DBは各プロジェクト側に保持し、company-hqには秘密情報を保存しない。
- 事業判断、KPI、顧客・市場仮説は company-hq 側の memory に集約する。

## 次アクション候補

1. X事業の目的とターゲット市場を定義する。
2. 北極星指標と週次KPIを決める。
3. 投稿カテゴリ、トーン、承認基準を整理する。
4. `wangan-agent` のメトリクスを事業レポート化する。
5. `x-poster` / `x-auto-post-agent` を残すか、`wangan-agent` に統合するか判断する。

## company-hqでの扱い

今後、company-hq の会話で「X事業」「X投稿」「湾岸ウォッチャー」「wangan-agent」と言った場合は、このメモと `~/Projects/wangan-agent` を前提に扱う。

担当部門の目安:

- 戦略: X事業計画、KPI、ポジショニング、投稿カテゴリ設計
- IT: `wangan-agent` / `x-poster` / X API 連携の実装・保守
- 営業: X経由のリード獲得、提案導線、商談化
- COO: 全体優先順位、週次運用、部門間統合
