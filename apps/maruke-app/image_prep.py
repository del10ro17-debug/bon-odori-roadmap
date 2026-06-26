"""Upload 画像の正規化（EXIF 回転・リサイズ）。"""

from __future__ import annotations

import io


def normalize_image(image_bytes: bytes, media_type: str = "image/jpeg") -> tuple[bytes, str]:
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
        max_edge = 2400
        if max(width, height) > max_edge:
            scale = max_edge / max(width, height)
            img = img.resize(
                (int(width * scale), int(height * scale)),
                Image.Resampling.LANCZOS,
            )

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, media_type
