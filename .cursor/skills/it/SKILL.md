---
name: it
description: >-
  Implements software, infrastructure, automation, and security practices. Use
  when the user mentions 開発, コード, API, デプロイ, CI, インフラ, 自動化, or technical
  architecture.
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# IT

## 担当範囲

- 設計・実装・レビュー・デバッグ
- リポジトリ構成、CI/CD、インフラ as code の提案
- 社内ツール連携（MCP・API・スクリプト）
- セキュリティの基本（秘密情報をコミットしない等）

## 手順

1. 要件・制約・既存スタックを確認
2. 小さく動く単位で実装（過剰設計を避ける）
3. 変更点・テスト方法・ロールバックを短く記載

## 設計メモテンプレート

```markdown
# [機能名] 技術メモ

## 目的
-

## 方針
-

## 変更ファイル（予定）
-

## テスト
- [ ] …

## リスク
-
```

## 品質基準

- プロジェクトの既存スタイルに合わせる
- `.env` や鍵はリポジトリに含めない
- 破壊的操作は CEO 確認後

## 他部門との接点

- 営業デモ → 最小 PoC を優先
- 経理連携 → ログ・監査証跡を意識
- 戦略の KPI → 計測イベント名を早期に合意
