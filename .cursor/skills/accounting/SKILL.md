---
name: accounting
description: >-
  Organizes expenses, invoices, cash flow, budgets, and financial summaries.
  Use when the user mentions 経費, 請求, 入金, 支払, 予算, P/L, キャッシュフロー,
  or tax-related bookkeeping prep (not legal tax advice).
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# 経理

## 担当範囲

- 経費・請求の整理とカテゴリ分け
- 入出金・キャッシュフローの簡易表
- 月次サマリのドラフト
- freee / マネーフォワード等への **入力用データ整形**（ツール連携は MCP 次第）

## 非担当（エスカレーション）

- 税務申告の最終判断 → 税理士
- 契約条項の解釈 → CEO + 専門家

## 手順

1. 期間・通貨・勘定方針を handbook から確認
2. 不足データを列挙（金額・日付・相手・証憑）
3. 表形式で整理 → 異常値・未払いをフラグ

## 経費一覧テンプレート

| 日付 | 内容 | 金額 | カテゴリ | 支払方法 | 証憑 |
|------|------|------|----------|----------|------|
| | | | | | |

## 月次サマリテンプレート

```markdown
# 月次サマリ YYYY-MM

## サマリ
- 売上:
- 費用:
- 粗利 / 営業利益:（算出可能な範囲）

## 注目
-

## CEO 確認事項
-
```

## 注意

数値は **出典ファイルまたは CEO 入力** を前提に。推測で確定額を書かない。
