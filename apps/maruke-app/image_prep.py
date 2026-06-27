"""Upload 画像の正規化（EXIF 回転・リサイズ）。"""

from __future__ import annotations

import io

WIDE_SPREAD_ASPECT = 1.25


def image_aspect_ratio(image_bytes: bytes) -> float | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            if height <= 0:
                return None
            return width / height
    except Exception:
        return None


def is_wide_spread(image_bytes: bytes, threshold: float = WIDE_SPREAD_ASPECT) -> bool:
    aspect = image_aspect_ratio(image_bytes)
    return aspect is not None and aspect >= threshold


def split_wide_spread(image_bytes: bytes, *, spine_ratio: float = 0.5) -> list[bytes]:
    """見開き1枚写真を左ページ・右ページに分割（左→右の順）。"""
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("画像分割に Pillow が必要です。") from exc

    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    width, height = img.size
    split_x = int(width * spine_ratio)
    split_x = max(int(width * 0.46), min(split_x, int(width * 0.54)))
    left = img.crop((0, 0, split_x, height))
    right = img.crop((split_x, 0, width, height))

    pages: list[bytes] = []
    for page in (left, right):
        buf = io.BytesIO()
        page.save(buf, format="JPEG", quality=94, optimize=True)
        pages.append(buf.getvalue())
    return pages


def normalize_image(
    image_bytes: bytes,
    media_type: str = "image/jpeg",
    *,
    max_edge: int = 2400,
    enhance_handwriting: bool = False,
    preserve_detail: bool = False,
) -> tuple[bytes, str]:
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return image_bytes, media_type

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        width, height = img.size
        if preserve_detail:
            edge_limit = max(max_edge, 4096)
        elif enhance_handwriting:
            edge_limit = max(max_edge, 4096)
        else:
            edge_limit = max_edge
        if max(width, height) > edge_limit:
            scale = edge_limit / max(width, height)
            img = img.resize(
                (int(width * scale), int(height * scale)),
                Image.Resampling.LANCZOS,
            )

        if enhance_handwriting:
            from PIL import ImageEnhance

            img = ImageEnhance.Contrast(img).enhance(1.22)
            img = ImageEnhance.Sharpness(img).enhance(1.3)

        buf = io.BytesIO()
        quality = 96 if preserve_detail else (94 if enhance_handwriting else 92)
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, media_type
