# 公庫申請書類パッケージ — まるつけ

- 更新: 2026-06-25
- 制度: **新規開業・スタートアップ支援資金**（日本政策金融公庫・国民生活事業）
- 公式様式: https://www.jfc.go.jp/n/service/dl_kokumin.html

---

## 申請サマリー（パターンA）

| 項目 | 記入値 |
|------|--------|
| 商号（案） | まるつけ株式会社 |
| 開業予定 | 2026年8月1日 |
| 代表報酬 | 35万円/月（固定） |
| 事務所 | 自宅兼事務所（按分1.5万/月） |
| 創業資金総額 | **1,600万円** |
| 自己資金 | **400万円** |
| 借入希望 | **1,200万円** |
| 返済 | 10年・元金据置6ヶ月（相談） |

---

## 書類一覧（この順で準備）

### Step 1 — CEO記入（【要CEO記入】を埋める）

| # | 書類 | ファイル | 提出 |
|---|------|----------|------|
| 1 | **創業計画書**（転記用） | [jfc-sougyou-plan-draft.md](./jfc-sougyou-plan-draft.md) | 公庫Excelへ転記 → PDF |
| 2 | **創業者経歴書** | [jfc-ceo-resume-draft.md](./jfc-ceo-resume-draft.md) | PDF |
| 3 | 借入申込書 | 公庫公式PDF | 記入 → PDF |

### Step 2 — 添付（推奨・審査用）

| # | 書類 | ファイル |
|---|------|----------|
| 4 | 事業概要書 | [jfc-business-overview.md](./jfc-business-overview.md) |
| 5 | 3年損益・資金計画 | [jfc-financial-plan.md](./jfc-financial-plan.md) |
| 6 | **月次キャッシュフロー** | [jfc-cashflow-scenarios.md](./jfc-cashflow-scenarios.md) |
| 7 | 設備見積明細 | [jfc-equipment-estimates.md](./jfc-equipment-estimates.md) |
| 8 | 市場・競合分析 | [market-analysis-2026-06-25.md](./market-analysis-2026-06-25.md) |
| 9 | 面談用1枚資料 | [jfc-supplement.html](./jfc-supplement.html)（印刷） |
| 10 | 面談Q&A | [jfc-interview-prep.md](./jfc-interview-prep.md) |

### Step 3 — 法人設立後

| 書類 | タイミング |
|------|-----------|
| 定款 | 設立時 |
| 登記簿謄本 | 設立後 |
| 事業用口座 | 設立後・自己資金400万入金 |
| 見積書（Mac等） | 面談前 |

### Step 4 — 手続き

| 順 | アクション | リンク |
|----|-----------|--------|
| 1 | 創業相談予約 | [公庫 創業相談](https://www.jfc.go.jp/n/service/heijitsu_soudan.html) |
| 2 | 創業計画書Excel転記 | 上記 Step 1 |
| 3 | オンライン申込 | 公庫サイト「お申込受付フォーム」 |
| 4 | 面談（2回程度） | 創業計画書 + 補足資料持参 |

---

## マスター・チェックリスト

→ [jfc-funding-prep.md](./jfc-funding-prep.md)

---

## 数値の正本

| 内容 | ファイル |
|------|----------|
| 月次CF・5パターン | [jfc-cashflow-scenarios.md](./jfc-cashflow-scenarios.md) |
| JSON（再計算） | `jfc-financial-model.json` |
| 再計算コマンド | `python3 tools/maruke_app/build_jfc_financial_model.py` |

---

## CEO記入チェック（申込前）

- [ ] 氏名・生年月日・住所・電話
- [ ] 学歴・資格
- [ ] 登記住所（自宅）
- [ ] 自己資金400万の出所
- [ ] 最寄り公庫支店
- [ ] 専業創業で記載するか（推奨: はい）
- [ ] 税理士レビュー（任意・推奨）
