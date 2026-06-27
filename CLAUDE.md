# company-hq — 仮想会社 HQ

このプロジェクトは坂倉翔が運営する仮想会社の本社です。
AGENTS.md に組織・スキル・アーキテクチャの詳細があります。

## Wiki Knowledge Base

Path: `/Users/sho_sakakura/Library/Mobile Documents/iCloud~md~obsidian/Documents/claude-obsidian`

**Obsidian wikiは坂倉翔の第二の脳。このプロジェクト内の情報と合わせて常に参照する。**

会話の冒頭または文脈が必要になった時点で以下の順で読む：

1. `wiki/hot.md` — まずここ（最近のトピック・進行中テーマ・約500語）
2. `wiki/index.md` — 全体地図
3. 関連ドメイン: `wiki/domains/<ドメイン>/`
4. 関連エンティティ: `wiki/entities/<名前>.md`（資産→ `sakakura-assets.md`、盆踊り→ `晴海盆踊り2026.md` 等）
5. 個別ページ — 必要なものだけ

**必ず参照するケース（義務）:**
- 事業・プロジェクト・資産・転職に関する質問
- 過去の意思決定・方針が関わる作業
- 人物・物件・企業名が出てきた時
- 「前に話した」「以前決めた」という言及
- company-hq内のファイルだけでは文脈が足りない時

**参照しないケース:** 純粋な一般的コーディング質問のみ

## Obsidian 同期ルール（必須）

会話・作業で以下の情報が更新・確定したら、**必ずObsidian wikiに反映する**：

| 情報の種類 | 保存先 |
|---|---|
| 資産情報（不動産・金融・家計） | `wiki/entities/sakakura-assets.md` を上書き更新 |
| 事業プロジェクトの進捗・意思決定 | `wiki/entities/<プロジェクト名>.md` + Git `status.md` |
| 新しい知識・学び | `wiki/domains/<該当ドメイン>/` |
| 日々の活動ログ | `wiki/log.md` に追記 |

**トリガー条件**（どれか1つでも該当したら保存）：
- 資産の数値・状況が変わった（物件売却・購入・残高更新等）
- 投資方針・ポリシーが変わった
- 事業の重要な意思決定があった
- ユーザーが「覚えておきたい」と感じそうな情報

ユーザーが「保存しない」と明示した場合のみスキップ。

`company/memory/` はポインタのみ。全文の二重管理禁止。詳細: `docs/knowledge-ssot.md`
