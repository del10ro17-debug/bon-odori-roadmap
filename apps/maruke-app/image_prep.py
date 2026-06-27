"""Upload 画像の正規化（EXIF 回転・リサイズ）。"""

from __future__ import annotations

import io


def normalize_image(
    image_bytes: bytes,
    media_type: str = "image/jpeg",
    *,
    max_edge: int = 2400,
    enhance_handwriting: bool = False,
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
        edge_limit = max(max_edge, 4096) if enhance_handwriting else max_edge
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
        quality = 94 if enhance_handwriting else 92
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, media_type
