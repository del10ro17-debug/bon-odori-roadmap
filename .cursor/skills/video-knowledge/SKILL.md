---
name: video-knowledge
description: >-
  Transcribes and summarizes YouTube videos and local video/audio files into
  structured Markdown. Use when the user mentions 動画, 文字起こし, トランスクリプト,
  video transcription, local video, meeting recording, or @video-knowledge.
compatibility: "Claude Code required. Python 3, ffmpeg, faster-whisper must be installed (see tools/video_knowledge/README or run setup in .venv)."
metadata:
  author: sho-sakakura
  version: "1.0.0"
---

# Video Knowledge

## 担当範囲

- YouTube URL の字幕取得・要約・Markdown 保存
- **ローカル動画/音声ファイル** の文字起こし（faster-whisper）・要約・Markdown 保存
- 出力先: `company/memory/videos/`

## 前提チェック

1. ファイルパスが存在するか（ローカル動画の場合）
2. 拡張子が対応形式か: `.mp4`, `.mov`, `.webm`, `.mkv`, `.m4a`, `.mp3`, `.wav`, `.aac`
3. `ffmpeg` がインストール済みか: `which ffmpeg`
4. venv がセットアップ済みか: `tools/video_knowledge/.venv`

未セットアップの場合は CEO に以下を案内:

```bash
brew install ffmpeg
cd tools/video_knowledge && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 手順 — ローカル動画

1. CEO から動画ファイルパス（またはワークスペース内パス）を受け取る
2. 長尺（10分超）の場合、CPU + `small` モデルで処理に数分〜十数分かかる旨を先に伝える
3. 実行:

```bash
cd tools/video_knowledge && source .venv/bin/activate
python process_local_video.py "/absolute/path/to/video.mp4" --title "任意タイトル"
```

4. 成功時、チャットで以下を報告:
   - 生成 Markdown のパス
   - Summary（要約）
   - Key Points（主要ポイント）
   - 文字起こしの先頭数行
5. 失敗時は `stderr` のエラーを要約し、ffmpeg 不足・形式非対応・venv 未構築など原因を特定

## 手順 — YouTube

```bash
cd tools/video_knowledge && source .venv/bin/activate
python process_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## 環境変数（任意）

| 変数 | 用途 |
|---|---|
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | LLM 要約 |
| `VIDEO_KNOWLEDGE_WHISPER_MODEL` | Whisper モデル（default: `small`） |
| `VIDEO_KNOWLEDGE_WHISPER_DEVICE` | `cpu` or `cuda` |

## 出力フォーマット

Markdown frontmatter に `source_type: local` または YouTube URL が含まれる。  
CEO への報告は日本語で、技術詳細は簡潔に。

## 他部門との接点

- 議事録として使う場合 → 秘書スキルと連携（アクションアイテム抽出）
- Notion 同期が必要な場合 → `--notion` フラグ（要 `NOTION_API_TOKEN`）
