# サッカーコーチアップ（soccer_coach_app）

- 状態: `active`
- 責任者: 坂倉
- 担当: IT
- 最終更新: 2026-07-22

## 2026-07-22 更新（消失リスク解消）

- **7/20 再実装を GitHub に確定**: SubjectAnchor 版一式が未コミット・未push（remote は7/15止まり）だったため commit＋push（`274672e`）。Qwen版消失に続く二度目の消失リスクを解消。
- **launch.json 追加**: `.claude/launch.json`（uvicorn `app:app` :8000）で起動を標準化。
- **要修繕**: `.venv` のシェバンが旧 `~/Projects/...` を指し破損。`rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` で再生成が必要。

## 概要

少年サッカー動画の家庭内解析エンジン。SubjectAnchor（候補1タップ確定 → 参照 crop 添付）付きで観察し、家庭向けレポートと丸囲みハイライトを出す。

## コード

- パス: `apps/soccer_coach_app/`（独立 git）
- Remote: `https://github.com/del10ro17-debug/sakakura-soccer-coach-app.git`

## 仕様・ナレッジ

- アプリ README: `apps/soccer_coach_app/README.md`
- Obsidian: `wiki/domains/サッカー-動画解析ノウハウ.md` / `wiki/domains/サッカー-コーチングカード.md`

## 完了済み

- SubjectAnchor 再実装（Mac 移行後）
- 家庭向けレポート + ハイライト
- テスト一式（fake Vision）

## 今すぐやること

| 優先 | 担当 | タスク | 期限 | 状態 |
|------|------|--------|------|------|
| P1 | IT | Vision=openai/fake で運用、MLX はモデル再配置後 | — | waiting |

## 起動（ローカル）

```bash
cd ~/company-hq/apps/soccer_coach_app
SOCCER_ANALYZER_FAKE=1 .venv/bin/python app.py   # テスト
.venv/bin/python app.py                          # 本番相当
```

## 未決事項

- MLX Qwen モデルの再配置タイミング

## 次回レビュー

ポートフォリオ週次で確認
