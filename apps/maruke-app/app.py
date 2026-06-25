"""まるつけ — FastAPI バックエンド。

  GET  /            … スマホ向け PWA（static/index.html）
  POST /api/grade   … 画像を受け取り採点結果 JSON を返す
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import grader

load_dotenv()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
BETA_INVITE_CODE = os.environ.get("BETA_INVITE_CODE", "").strip()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_BYTES = 15 * 1024 * 1024
MAX_ANSWER_IMAGES = 6
VALID_GRADES = {"1", "2", "3", "4", "5", "6"}
VALID_GRADING_MODES = {"simple", "rich"}


app = FastAPI(title="まるつけ")


@app.get("/api/health")
async def api_health():
    return {
        "ok": True,
        "live_grading": bool(os.environ.get("OPENAI_API_KEY")),
        "invite_required": bool(BETA_INVITE_CODE),
    }


@app.get("/api/config")
async def api_config():
    return {
        "invite_required": bool(BETA_INVITE_CODE),
        "plans": {
            "simple": {
                "label": "答えだけ",
                "price_hint": "月600円想定",
                "scans_hint": "月120回",
                "description": "○×と正解だけ。サクッと丸つけ。",
            },
            "rich": {
                "label": "解説リッチ",
                "price_hint": "月1,280円想定",
                "scans_hint": "月60回",
                "description": "ママ向け解説・子どもヒント・図形の図つき。",
            },
        },
    }


@app.post("/api/grade")
async def api_grade(
    images: Optional[list[UploadFile]] = File(None),
    image: Optional[UploadFile] = File(None),
    subject: Optional[str] = Form(None),
    grade_level: Optional[str] = Form(None),
    answer_key: Optional[UploadFile] = File(None),
    invite_code: Optional[str] = Form(None),
    grading_mode: Optional[str] = Form("rich"),
):
    if BETA_INVITE_CODE and (invite_code or "").strip() != BETA_INVITE_CODE:
        return JSONResponse({"error": "招待コードが正しくありません。"}, status_code=403)

    mode = (grading_mode or "rich").strip()
    if mode not in VALID_GRADING_MODES:
        return JSONResponse({"error": "採点モードが不正です。"}, status_code=400)

    answer_uploads = [upload for upload in (images or []) if upload.filename]
    if image is not None and image.filename:
        answer_uploads.insert(0, image)

    if not answer_uploads:
        return JSONResponse({"error": "答案写真を1枚以上選んでください。"}, status_code=400)
    if len(answer_uploads) > MAX_ANSWER_IMAGES:
        return JSONResponse(
            {"error": f"答案写真は最大{MAX_ANSWER_IMAGES}枚までです。"},
            status_code=400,
        )

    normalized_grade = (grade_level or "").strip()
    if normalized_grade and normalized_grade not in VALID_GRADES:
        return JSONResponse({"error": "学年は小1〜小6から選んでください。"}, status_code=400)

    answer_images = []
    for upload in answer_uploads:
        answer_bytes = await upload.read()
        if len(answer_bytes) > MAX_BYTES:
            return JSONResponse({"error": "画像が大きすぎます（1枚15MBまで）。"}, status_code=413)
        media_type = upload.content_type or "image/jpeg"
        if media_type not in ALLOWED_TYPES:
            media_type = "image/jpeg"
        answer_images.append((answer_bytes, media_type))

    key_bytes = None
    key_media_type = None
    if answer_key is not None and answer_key.filename:
        key_bytes = await answer_key.read()
        if len(key_bytes) > MAX_BYTES:
            return JSONResponse({"error": "解答画像が大きすぎます（15MBまで）。"}, status_code=413)
        key_media_type = answer_key.content_type or "image/jpeg"
        if key_media_type not in ALLOWED_TYPES:
            key_media_type = "image/jpeg"

    if not os.environ.get("OPENAI_API_KEY"):
        return grader.demo_result(
            subject_hint=subject or None,
            grade_level=normalized_grade or None,
            grading_mode=mode,
        )

    try:
        result = grader.grade(
            answer_images=answer_images,
            subject_hint=subject or None,
            grade_level=normalized_grade or None,
            key_image=key_bytes,
            key_media_type=key_media_type,
            grading_mode=mode,
        )
    except grader.GraderError as e:
        return JSONResponse({"error": str(e)}, status_code=502)

    return result


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
