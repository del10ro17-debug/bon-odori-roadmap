"""まるつけ — FastAPI バックエンド。

  GET  /            … スマホ向け PWA（static/index.html）
  POST /api/grade   … 画像を受け取り採点結果 JSON を返す
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import grader
from image_prep import normalize_image

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("maruke.app")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
BETA_INVITE_CODE = os.environ.get("BETA_INVITE_CODE", "").strip()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_BYTES = 15 * 1024 * 1024
MAX_ANSWER_IMAGES = 6
MAX_PROBLEM_IMAGES = 4
VALID_GRADES = {"1", "2", "3", "4", "5", "6"}
VALID_GRADING_MODES = {"simple", "rich"}


app = FastAPI(title="まるつけ")


@app.get("/api/health")
async def api_health():
    return {
        "ok": True,
        "live_grading": bool(os.environ.get("OPENAI_API_KEY")),
        "invite_required": bool(BETA_INVITE_CODE),
        "models": {
            "fast": grader.OPENAI_FAST_MODEL,
            "precise": grader.OPENAI_PRECISE_MODEL,
            "ocr": grader.OPENAI_OCR_MODEL,
        },
        "split_two_stage": grader.SPLIT_TWO_STAGE,
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


async def _read_uploads(
    uploads: list[UploadFile] | None,
    *,
    label: str,
    enhance_handwriting: bool = False,
) -> tuple[list[tuple[bytes, str]], JSONResponse | None]:
    images: list[tuple[bytes, str]] = []
    for upload in uploads or []:
        if not upload.filename:
            continue
        raw = await upload.read()
        if len(raw) > MAX_BYTES:
            return [], JSONResponse(
                {"error": f"{label}が大きすぎます（1枚15MBまで）。"},
                status_code=413,
            )
        media_type = upload.content_type or "image/jpeg"
        if media_type not in ALLOWED_TYPES:
            media_type = "image/jpeg"
        normalized, media_type = normalize_image(
            raw, media_type, enhance_handwriting=enhance_handwriting
        )
        images.append((normalized, media_type))
    return images, None


@app.post("/api/grade")
async def api_grade(
    images: Optional[list[UploadFile]] = File(None),
    image: Optional[UploadFile] = File(None),
    problem_images: Optional[list[UploadFile]] = File(None),
    subject: Optional[str] = Form(None),
    grade_level: Optional[str] = Form(None),
    answer_key: Optional[UploadFile] = File(None),
    invite_code: Optional[str] = Form(None),
    grading_mode: Optional[str] = Form("rich"),
    layout_mode: Optional[str] = Form("combined"),
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

    problem_uploads = [upload for upload in (problem_images or []) if upload.filename]
    if len(problem_uploads) > MAX_PROBLEM_IMAGES:
        return JSONResponse(
            {"error": f"問題プリントは最大{MAX_PROBLEM_IMAGES}枚までです。"},
            status_code=400,
        )

    layout = (layout_mode or "combined").strip()
    if layout == "split" and not problem_uploads:
        return JSONResponse(
            {"error": "「問題と答案が別」の場合は問題プリントも撮影してください。"},
            status_code=400,
        )

    normalized_grade = (grade_level or "").strip()
    if normalized_grade and normalized_grade not in VALID_GRADES:
        return JSONResponse({"error": "学年は小1〜小6から選んでください。"}, status_code=400)

    answer_images, answer_err = await _read_uploads(
        answer_uploads, label="答案写真", enhance_handwriting=True
    )
    if answer_err:
        return answer_err

    problem_image_data, problem_err = await _read_uploads(problem_uploads, label="問題プリント")
    if problem_err:
        return problem_err

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
        logger.info(
            "grade request layout=%s mode=%s grade=%s problems=%d answers=%d key=%s",
            layout,
            mode,
            normalized_grade or "-",
            len(problem_image_data),
            len(answer_images),
            bool(key_bytes),
        )
        result = grader.grade(
            answer_images=answer_images,
            problem_images=problem_image_data or None,
            subject_hint=subject or None,
            grade_level=normalized_grade or None,
            key_image=key_bytes,
            key_media_type=key_media_type,
            grading_mode=mode,
        )
    except grader.GraderError as e:
        logger.warning("grade failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=502)

    logger.info(
        "grade ok strategy=%s items=%d correct=%d incorrect=%d",
        result.get("grading_strategy", "?"),
        result.get("total", 0),
        result.get("correct_count", 0),
        result.get("incorrect_count", 0),
    )
    return result


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
