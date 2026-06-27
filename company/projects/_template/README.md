# 新規プロジェクト チェックリスト

`company/projects/_template/` をコピーして `[project-id]/` を作成する。

## セットアップ

- [ ] `project-id` を kebab-case で決める（例: `bon-odori-harumi-2026`）
- [ ] `status.md` に概要・今すぐ・未決・リスクを記入
- [ ] `company/projects/registry.yaml` に登録
- [ ] 継続作業が見込まれる場合:
  - [ ] `AGENT_CONTEXT.md` を status から要約（200行以内）
  - [ ] `.cursor/rules/[project-id]-light-chat.mdc` を作成
  - [ ] `company/projects/README.md` の一覧を更新

## 運用

- 決定・タスク変更 → **必ず `status.md` を先に更新**
- 週1または大きな決定時 → `AGENT_CONTEXT.md` を status と同期
- 週次 PMO → `_portfolio/status.md` を各 status から集約

## 軽量チャット rule の雛形

```yaml
---
description: [プロジェクト名]の軽量Agentチャット用
globs: company/projects/[project-id]/**
alwaysApply: false
---

# [プロジェクト名] — 軽量チャット

## 必須

1. 前提は `AGENT_CONTEXT.md` と必要最小限の `status.md` のみ
2. **禁止**: `agent-transcripts` の読取
3. 更新時は `status.md` を先に反映

## 新チャット一行

@...-light-chat @company/projects/[project-id]/AGENT_CONTEXT.md を前提に。transcripts 読まないで。
```

## 参考

- 成功例: `bon-odori-harumi-2026/` + `@bon-odori-light-chat`
- チャット運用: [docs/agent-playbook.md](../../docs/agent-playbook.md)
