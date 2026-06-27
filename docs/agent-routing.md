# 話題別エージェント早見表

> **組織図**: [company-org-chart.html](company-org-chart.html)  
> **使い方**: 新しい Agent チャットを開き、下の **最初の一行** をコピペして送る。  
> ルール名（`@xxx-light-chat`）を付けると、その話題専用のエージェントとして動く。

---

## 迷ったら

| 状況 | 依頼先 |
|------|--------|
| 何の話題かはっきりしている | 下表の **専用ルール** |
| 複数部門・方針判断・よくわからない | **COO**（ルールなしで「COO、…」） |
| コード1件だけ直したい | **`@it`** を先頭に |

---

## 話題 → エージェント対応表

| 話題 | ルール（@で指定） | スキル | 最初の一行（コピペ用） |
|------|-------------------|--------|------------------------|
| **盆踊り2026・出店運営** | `@bon-odori-light-chat` | Event Ops | `@bon-odori-light-chat @company/projects/bon-odori-harumi-2026/AGENT_CONTEXT.md を前提に。agent-transcripts は読まないで。` |
| **X投稿・湾岸ウォッチャー文案** | `@x-business-light-chat` | 戦略 / 営業 | `@x-business-light-chat @company/projects/x-business/AGENT_CONTEXT.md を前提に。` |
| **Instagram投稿・湾岸暮らしメモ** | `@instagram-light-chat` | 戦略 / 営業 | `@instagram-light-chat @company/projects/instagram-business/AGENT_CONTEXT.md を前提に。` |
| **Xへ実際に投稿（UI）** | ※Cursor外 | — | `~/Projects/wangan-agent` で `npm start` → http://localhost:3000/ |
| **湾岸マンション・時価・坪単価** | `@wangan-price-light-chat` | 湾岸不動産 | `@wangan-price-light-chat @docs/wangan-price-db.md を前提に。` |
| **保有物件の売却判断** | `@wangan-price-light-chat` | 湾岸不動産 | `@wangan-price-light-chat 晴海フラッグ SEA VILLAGE 1205 の時価と売却判断を出して。` |
| **沖縄民泊・物件精査** | `@okinawa-minpaku-light-chat` | 沖縄民泊 / 戦略 / 経理 | `@okinawa-minpaku-light-chat @company/projects/okinawa-minpaku/AGENT_CONTEXT.md を前提に。agent-transcripts は読まないで。` |
| **まるつけ・公庫・採点精度** | `@maruke-light-chat` | IT / 戦略 | `@maruke-light-chat @company/projects/maruke-app/AGENT_CONTEXT.md を前提に。agent-transcripts は読まないで。` |
| **動画・文字起こし・YouTube要約** | `@video-knowledge-light-chat` | 動画ナレッジ | `@video-knowledge-light-chat この動画を文字起こしして: /path/to/file.mp4` |
| **Notion・議事録・タスクDB** | `@notion-ops-light-chat` | 秘書 / IT | `@notion-ops-light-chat @company/projects/notion-operations/status.md を前提に。` |
| **日程・議事録・メール下書き** | `@secretary-light-chat` | 秘書 | `@secretary-light-chat 以下を議事録にして。決定事項とToDoを分けて:` |
| **湾岸ファミリーアプリ開発** | `@wangan-family-light-chat` | IT / 戦略 | `@wangan-family-light-chat @apps/wangan-family-app/README.md を前提に。` |
| **コード・バグ・CI** | `@it`（Direct） | IT | `@it このエラーを直して:（ログを貼る）` |
| **グラフ・データ可視化・図** | COO または `@creative-visual` | クリエイティブ／可視化 | `COO、湾岸価格DBからエリア別坪単価のグラフを作って。` |
| **絵・チラシ・ロゴ・アイコン** | COO または `@creative-visual` | クリエイティブ／可視化 | `COO、盆踊りの告知チラシ画像を作って。` |
| **週次・優先順位・複数案件** | `@pmo` | PMO | `@pmo ポートフォリオ更新して。` |
| **経費・請求・数値整理** | COO または `@accounting` | 経理 | `COO、今月の経費をカテゴリ別に整理して。` |
| **提案・商談・顧客** | COO または `@sales` | 営業 | `COO、〇〇社向け提案の骨子を作って。` |
| **事業計画・KPI・競合** | COO または `@strategy` | 戦略 | `COO、X事業のKPI案を2パターン出して。` |

---

## 外部ツール（Cursor Agent ではない）

| やりたいこと | 場所 | 起動 |
|-------------|------|------|
| X投稿（生成・承認・投稿） | wangan-agent | `cd ~/Projects/wangan-agent && npm start` |
| 湾岸価格ダッシュボード | company-hq | Finder で `open_wangan_dashboard.command` |
| 湾岸ファミリーアプリ（実機確認） | company-hq | `open_wangan_family_app.command` |

---

## チャットを分ける目安

- **別の話題** → 新チャット + 上表のルール
- **同じ案件の続き** → 同チャット（コンテキスト70%超えたら新チャット + `AGENT_CONTEXT.md`）
- **文案だけ Cursor、投稿は自分** → `@x-business-light-chat` → 文案コピー → wangan-agent UI

---

## ファイル一覧

| ルール | 定義ファイル |
|--------|-------------|
| `@bon-odori-light-chat` | [.cursor/rules/bon-odori-light-chat.mdc](../.cursor/rules/bon-odori-light-chat.mdc) |
| `@x-business-light-chat` | [.cursor/rules/x-business-light-chat.mdc](../.cursor/rules/x-business-light-chat.mdc) |
| `@instagram-light-chat` | [.cursor/rules/instagram-light-chat.mdc](../.cursor/rules/instagram-light-chat.mdc) |
| `@wangan-price-light-chat` | [.cursor/rules/wangan-price-light-chat.mdc](../.cursor/rules/wangan-price-light-chat.mdc) |
| `@okinawa-minpaku-light-chat` | [.cursor/rules/okinawa-minpaku-light-chat.mdc](../.cursor/rules/okinawa-minpaku-light-chat.mdc) |
| `@video-knowledge-light-chat` | [.cursor/rules/video-knowledge-light-chat.mdc](../.cursor/rules/video-knowledge-light-chat.mdc) |
| `@notion-ops-light-chat` | [.cursor/rules/notion-ops-light-chat.mdc](../.cursor/rules/notion-ops-light-chat.mdc) |
| `@secretary-light-chat` | [.cursor/rules/secretary-light-chat.mdc](../.cursor/rules/secretary-light-chat.mdc) |
| `@wangan-family-light-chat` | [.cursor/rules/wangan-family-light-chat.mdc](../.cursor/rules/wangan-family-light-chat.mdc) |
| `@maruke-light-chat` | [.cursor/rules/maruke-light-chat.mdc](../.cursor/rules/maruke-light-chat.mdc) |

詳細運用: [agent-playbook.md](agent-playbook.md)
