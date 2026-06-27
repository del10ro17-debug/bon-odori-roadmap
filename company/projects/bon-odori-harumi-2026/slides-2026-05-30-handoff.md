# 5/30 認識合わせ — 資料制作 受け渡しパッケージ

> **このファイル一式を Claude Artifacts / 別チャット / デザイナーに渡せば、議論内容を再現できます。**  
> 自動生成 PPTX（`assets/2026-05-30-alignment.pptx`）は python-pptx の見た目限界で品質が低い。**HTML版または Artifacts 版を推奨。**

---

## ファイル一覧（受け渡しセット）

| ファイル | 用途 |
|---------|------|
| **`slides-2026-05-30-handoff.md`** | 本ファイル（使い方 + Artifacts プロンプト） |
| **`slides-2026-05-30-data.json`** | 機械可読：全17スライド・色・人名・宿題・タイムライン |
| **`assets/2026-05-30-alignment.docx`** | **Word / Google Docs 用（推奨）** |
| **`slides-2026-05-30-deck.html`** | ブラウザ投影用 |
| `slides-2026-05-30-script.md` | 台本・Speaker Notes |
| `assets/2026盆踊り大会_会場図.pdf.png` | 会場図（スライド5用） |

---

## 今夜すぐ使う（ターミナル不要）

### HTML スライドを開く

Finder → `⌘⇧G` → 以下を貼り付け → `slides-2026-05-30-deck.html` をダブルクリック

```
/Users/sho_sakakura/company-hq/company/projects/bon-odori-harumi-2026
```

**操作**: `→` / `←` または クリックでページ送り · `F` で全画面

### ターミナルなら1行

```bash
open "/Users/sho_sakakura/company-hq/company/projects/bon-odori-harumi-2026/slides-2026-05-30-deck.html"
```

---

## Claude Artifacts に渡す方法

### 手順

1. [Claude](https://claude.ai) で新規チャット（Artifacts 有効）
2. 下記 **「Artifacts 用プロンプト（全文コピー）」** を貼り付け
3. 続けて **`slides-2026-05-30-data.json` の全文** を貼る（または「JSONを添付」と書いてファイル内容を貼る）
4. 「React/HTML のスライドデッキを Artifact で作って」と依頼
5. 完成 Artifact を PDF 化 or 全画面投影

### Artifacts 用プロンプト（全文コピー）

```text
晴海盆踊り2026の5/30認識合わせMTG用プレゼンを、Claude Artifact（HTML/React）で作ってください。

## 要件
- 16:9、17スライド、1スライド1メッセージ
- 日本語、Noto Sans JP
- 左上に色ラベル帯：確定 #197A4B / 今夜決める #E65100 / これから #0017C1 / 注意 #CE0000
- キーボード ← → でページ送り、全画面対応
- スライド7は「必要人数」空欄表（その場記入用）
- スライド9は横タイムライン
- 人名：ローマ字（Sho Sakakura等）またはひらがな（ゆうや、たくろう）

## コンテンツ
添付の slides-2026-05-30-data.json を唯一のソースとして全スライドを生成してください。
JSON の slides 配列、timeline、readinessChecklist、homework、risks をすべて反映。

## デザイン
- 白背景、余白多め、見出し大きく
- 表は見やすい zebra striping
- チーム向けで「わかりやすい」が最優先（装飾より可読性）
- python-pptx で作った簡素なPPTXの改善版

## 今夜の主決定
各チーム×7/11・7/12の必要人数 → 不足分の可視化

## 出力
単一 Artifact（HTML）。Speaker Notes は各スライド下部に小さく表示可。
```

---

## コード側で作り直す場合

### データソース

`slides-2026-05-30-data.json` が正（Single Source of Truth）

### 既存スクリプト

| スクリプト | 出力 | 品質 |
|-----------|------|------|
| `tools/bon_odori_attendance/build_alignment_slides.py` | PPTX | 低（見た目簡素） |
| `slides-2026-05-30-deck.html` | HTML | **高（推奨）** |

### JSON から HTML を再生成したい場合

```bash
# 将来: build_alignment_deck.py を JSON 読み込みに統一可能
open company/projects/bon-odori-harumi-2026/slides-2026-05-30-deck.html
```

---

## 議論の要約（コンテキスト）

### イベント

- 晴海ふ頭公園盆踊り2026 / 7/11–12 / 37番ケバブ / ユーアンドショー出店
- 5/30 19:30 坂倉家 · 60分 · 6/13まで準備完結が目標

### 今夜決める

1. 各チーム × 7/11・7/12 の**必要人数（安心ライン）**
2. **不足人数** → 追加募集
3. 論点整理：テントレイアウト、当日準備、PayPay、デイリースケジュール、ソフトドリンク

### 確定済み

- 許認可OK、ケバブ、電源のみ、37番、搬入13時〜、PayPay基本

### 人名表記ルール

- フルネーム判明 → ローマ字（Sho Sakakura, Hiro Takeyama, Nozomi Aoshima）
- 漢字未確認 → ひらがな（ゆうや、たくろう、りさ）
- 本文 → 名前+さん

---

## Cursor 別チャットへの渡し方

新規 Agent チャットで:

```
@bon-odori-light-chat
company/projects/bon-odori-harumi-2026/slides-2026-05-30-handoff.md
company/projects/bon-odori-harumi-2026/slides-2026-05-30-data.json
を読んで、スライド資料を改善して。
```

---

## Google Slides 化

1. HTML をブラウザ全画面で投影（今夜） **または**
2. Artifacts 完成版を PDF → Google Slides にインポート **または**
3. Artifacts / HTML を参考に Slides を手作業

---

## MTG後

`status.md` の「5/30 MTG 資料」に必要人数・不足分を追記。  
スライド7の記入結果を JSON または HTML に反映すると次回 MTG に再利用可。
