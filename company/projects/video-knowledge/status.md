# Video Knowledge Pipeline

- 状態: **MVP implemented & verified**
- 主管: IT / COO
- 目的: YouTube視聴内容・ローカル動画をAI向けMarkdown/Notionに自動蓄積

## 実装済み

| コンポーネント | パス | 状態 |
|---|---|---|
| CLI処理 (YouTube) | `tools/video_knowledge/process_video.py` | 動作確認済 |
| CLI処理 (ローカル) | `tools/video_knowledge/process_local_video.py` | 実装済 |
| 音声抽出 | `tools/video_knowledge/audio_extract.py` | 実装済 |
| ローカルSTT | `tools/video_knowledge/stt.py` (faster-whisper) | 実装済 |
| ローカルAPI | `tools/video_knowledge/server.py` (:8787) | 動作確認済 |
| Chrome拡張 | `apps/video-capture-extension/` | 実装済 |
| Markdown出力 | `company/memory/videos/` | 動作確認済 |
| Cursorスキル | `.cursor/skills/video-knowledge/SKILL.md` | 実装済 |
| Notionスキーマ | `company/projects/notion-operations/notion-schema.md` §動画メモ | 定義済 |

## 動作確認 (2026-05-25)

```bash
# YouTube CLI
cd tools/video_knowledge && source .venv/bin/activate
python process_video.py "https://www.youtube.com/watch?v=VIDEO_ID"

# ローカル動画 CLI
python process_local_video.py "/path/to/video.mp4"

# サーバー
python server.py
curl http://127.0.0.1:8787/health
```

- 字幕取得 → 簡易要約（LLM未設定時）→ Markdown 保存まで確認
- ingest API 経由の保存も確認

## CEOセットアップ

1. `brew install ffmpeg`（ローカル動画用）
2. `cd tools/video_knowledge && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. `ANTHROPIC_API_KEY` または `OPENAI_API_KEY` を設定（任意、未設定時は簡易要約）
4. Notion連携する場合: `NOTION_API_TOKEN`, `NOTION_VIDEO_DB_ID`
5. `python server.py` を起動（YouTube Chrome拡張用）
6. Chrome → `chrome://extensions` → Load unpacked → `apps/video-capture-extension/`

### ローカル動画の使い方

Cursor チャット:

```
@video-knowledge この動画を文字起こしして
/Users/.../meeting.mp4
```

または CLI:

```bash
python process_local_video.py "/path/to/meeting.mp4" --title "定例MTG"
```

## Notion DB

`notion-schema.md` の「動画メモ」DBを Notion に手動作成してください。

## 残タスク

- [ ] `weekly_digest.py` — 週次ダイジェスト生成（未実装）
- [ ] `start-server.sh` — ワンコマンド起動（未実装）
- [ ] 1週間パイロット運用
- [ ] LLM要約品質チューニング（APIキー設定後）
- [ ] Notion DB 作成 + 連携テスト
- [ ] ローカル動画 E2E テスト（短尺サンプル）
