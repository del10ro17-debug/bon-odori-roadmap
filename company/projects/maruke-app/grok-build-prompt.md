# まるつけ — Grok Build Mode 用プロンプト

- 作成: 2026-08-19
- 目的: 既存の FastAPI 試作の仕様を引き継ぎ、**Grok Build** で動く親向けプロトタイプを作る
- 対象: grok.com / Grok アプリ → モード切替 **Build**
- スコープ: P0 のみ（写真→丸つけ / 未記入→解答例）。弱点分析・課金・ログインは作らない

## 使い方

1. grok.com または Grok アプリを開く
2. モード切替で **Build** を選ぶ
3. 下の **初回プロンプト** をそのまま貼る
4. プレビューが出たら、実プリントの写真で1回試す
5. 足りない点は、同じ会話に **続きプロンプト** を1本ずつ貼る（まとめ貼りしない）

注意:

- これは本番ではなく、**夕方5分で使える見た目と採点ルールの試作**
- 子どもの答案写真はクラウド履歴に残さない
- 「全問一瞬・全教科完璧」は約束しない

---

## 初回プロンプト（全文コピー）

```
Build a working mobile-first Japanese web app named 「まるつけ」. This is a parent tool, not a kids learning game.

PRODUCT
中学受験家庭の保護者が、塾・進研・Z会の宿題を撮るだけで丸つけできるアプリ。
既存の FastAPI + Vision 試作の仕様を引き継ぐ。Grok Build で動くプロトタイプを今すぐ作れ。
OpenAI API キーは使わない。Grok 自身の画像理解（vision）で答案を読む。

WHO
Primary user: 共働きの保護者。小4〜小6の中学受験。毎晩の丸つけがボトルネック。
Use it in 5 minutes after dinner, on a phone, with one thumb.

WHAT IT DOES (P0 ONLY)
1. 学年（小4 / 小5 / 小6）と教科（算数 / 国語 / 理科 / 社会）を選ぶ
2. 答案写真を撮る、またはカメラロールから選ぶ（最大6枚）
3. 任意で解答ページ写真も添付できる
4. 「丸つけする」を押す
5. 設問ごとに ⭕️ / ❌ / 🟡 / ✏️解答例 を出す

CRITICAL RULES — follow exactly
- 手書きの答えがある → result_type = graded。正誤を判定する
- 未記入・空欄 → result_type = answer_example。×にしない。correct_answer に保護者がそのまま使える解答例を書く。child_answer は「（未記入）」
- 読めない文字、見開きで潰れている、記述・作文で自信がない → verdict = uncertain（🟡）。勝手に×にしない
- 解答ページが添付されている → それを正とする（basis = answer_key）。無いときは Grok が解く（basis = solved）
- Never invent a child's answer. If you cannot read it, mark 🟡
- Never promise 100% accuracy. 🟡 is a feature, not a failure

SCREENS
1) Home
- Large title: まるつけ
- Sub: 中学受験の宿題、撮るだけで丸つけ。
- Grade chips, subject chips
- Giant primary button: 答案を撮る / 写真を選ぶ
- Secondary: 解答ページを付ける（任意）
- Tiny tip: 「見開きより、1ページずつ撮ると精度が上がります」
- Text button: サンプルで試す（実写真なしでUI確認用）

2) Confirm
- Thumbnails of selected photos
- Add more / delete
- Optional crop handles if easy; otherwise skip crop
- Button: 丸つけする
- If 2+ pages look like a spread, show warning: 片ページずつ撮ると読み取りが安定します

3) Processing
- Honest status text, not a spinner-only screen
- 「答え合わせ中…」 if handwriting detected
- 「未記入の問題は解答例を作成中…」
- ETA style: 十数秒かかることがあります

4) Results
- Summary chips: ⭕️n  ❌n  🟡n  ✏️n
- List of questions:
  number, short question summary, child_answer, correct_answer, verdict
- 🟡 items are visually distinct and labeled 要確認（親が最終判断）
- ✏️ items labeled 解答例
- Tap a row to expand: 判定理由を1〜2行、記述なら観点コメント
- Parent can tap 🟡 and override to ⭕️ or ❌ (local only)
- Button: 別の宿題を丸つけ

GRADING OUTPUT (internal)
Each item must have:
- number
- question (short)
- child_answer
- correct_answer
- verdict: correct | incorrect | uncertain
- result_type: graded | answer_example | unreadable
- basis: answer_key | solved
- note (short, Japanese)

VISION BEHAVIOR
When the user uploads photos, actually analyze the images with Grok vision.
Do not return random dummy scores for real photos.
For 「サンプルで試す」 only, use this fixed demo (label it デモ):
  小5 算数、3問
  1. つるとかめ 合わせて10匹、足28本。つるは何羽？ 子: 6羽 → ⭕️ 正解 6羽
  2. 12÷3 正しいものを選べ ア4 イ36 ウ6。子: イ → ❌ 正解 ア
  3. 正方形の1辺6cm。周の長さは？ 子: （未記入） → ✏️ 解答例 24cm
If this Build environment cannot call vision on uploaded photos, keep the full UI and show a clear banner:
「このプレビューでは実写真の採点が使えない場合があります。サンプルでUIを確認し、実採点は写真を添付して再実行してください。」
Never silently fake a perfect score.

DESIGN
- Japanese only UI
- Mobile-first, one column, max-width ~430px centered on desktop
- Parent evening tool: off-white background, ink/navy text, one accent (deep blue)
- NOT a colorful kids edutainment app. No mascots, no pastels, no confetti, no points/stars
- Huge tap targets (min 44px)
- System Japanese font
- Quiet, trustworthy, fast-looking
- Results must be readable at a glance while standing in the kitchen

DO NOT BUILD
- Login, signup, paywall
- Cloud history of children's answer photos
- Weakness charts, weekly coaching, 塾代替
- English UI
- Fake testimonials
- Settings jungle

PRIVACY
Process photos in-session only. Do not persist homework images. If you keep anything, keep text-only results in memory for this session.

First version must be a clickable working app, not a landing page.
```

---

## 同じ会話に貼る続き（1本ずつ）

プレビューが出たあと、実写真を1枚投げて挙動を見てから使う。

### 2. 採点ルールを固定する

```
採点ロジックを厳格化して。実写真を採点するとき、次を絶対に守って。

1. 設問を上から番号順に全部出す。飛ばさない。
2. 子どもの手書きが空、薄い、消しゴム跡だけなら未記入扱い。×にしない。解答例を出す。
3. 記述・作文・「考えを書きましょう」は 🟡 + 解答例 + 観点（含めてほしい要素を箇条書き2〜4個）。無理に配点しない。
4. 選択問題（ア〜エ）は、枠に書かれた記号を優先して読む。
5. 自信が70%未満なら 🟡。誤採点するより親に委ねる。
6. 見開き1枚で本文と問題が両方写っている場合は、問題ページ側を優先し、読み取れない設問は unreadable にする。
7. 結果リストの各行に「根拠: 解答ページ / AIが解いた」を小さく出す。

UIはそのまま。ダミー点数は禁止。
```

### 3. スマホの夕方UX

```
保護者が片手で使えるようにUIを直して。

- 最初の画面の主ボタンを画面下に固定（答案を撮る）
- 写真確認画面で、サムネを横スクロール。追加は「+」
- 処理中は戻れる。ただし二重送信は防ぐ
- 結果は大きく: ⭕️❌🟡✏️ を行の左に 28px 以上
- 要確認（🟡）をリスト先頭にまとめるトグルを付ける
- エラー時は「写真が読めませんでした。1ページだけ、明るい場所で撮り直してください」と具体的に出す
- 見開き警告はアップロード直後に出す
- 学年・教科の選択は、一度選んだらそのセッション中は覚えている
```

### 4. 国語・記述の扱い

```
国語プリント対応を足して。

- 選択（ア〜エ）: 通常採点
- 穴埋め・漢字: 通常採点。表記ゆれ（全角半角、句点の有無）は 🟡 にせず、意味が同じなら ⭕️
- 字数指定の短文: 解答例 + 観点。字数オーバー/不足が明らかなら note に書くが、勝手に×にしない
- 長文記述: 必ず 🟡。解答例は「模範」ではなく「要素を含む例」とラベルする
- 縦書き本文が写っている場合は、設問ページを優先。本文は設問理解の参考にだけ使う

サンプルで試す に、国語1問（選択⭕️）と記述1問（✏️）を追加して。
```

### 5. 公開前の仕上げ

```
publish できる状態にして。

- タイトル: まるつけ
- 説明: 中学受験の宿題を撮って丸つけ。未記入なら解答例。要確認は親が判断。
- 初回オンボーディングは3枚まで:
  1. 撮る
  2. ⭕️❌🟡 / 未記入は解答例
  3. 🟡は親が最終判断。見開きより1ページずつ
- 空状態・権限拒否（カメラ）・写真0枚で送信、の3エラーを丁寧に
- フッターに小さく: 試作です。誤採点の可能性があります。個人情報を含む答案の共有はしないでください。
- 子供の顔が写りそうな写真の注意は出さない（過剰）。答案写真の保存をしないことだけ書く
```

---

## 試すときのチェック（CEO）

| 確認 | 合格の目安 |
|------|------------|
| サンプルで試す | 3問が ⭕️❌✏️ で分かれて出る |
| 塾算数 1ページ | 設問が抜けない。誤採点より 🟡 が多いのは可 |
| 未記入の計算 | × ではなく ✏️解答例 |
| 国語の記述 | 🟡 + 観点。いきなり×にしない |
| 見開き | 警告が出る。読めない設問は 🟡 |

P0完了の目安（既存プロトコルと同じ）: 明らかな誤りが各ページ1問以下、または 🟡 で逃げている。

---

## この試作の位置づけ

| 層 | 役割 |
|----|------|
| **Grok Build** | 今やる。親UXと採点ルールのクリックできる試作。共有リンクで実プリント検証 |
| **company-hq `apps/maruke-app/`** | 正本の実装（FastAPI）。精度テスト・公庫・本番はこちら |
| やらない | grok.me を本番課金プロダクトにする。答案画像のクラウド履歴 |
