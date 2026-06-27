"""PDF を採点用 JPEG ページ列に変換する。"""

from __future__ import annotations

import io


def pdf_to_jpeg_pages(
    pdf_bytes: bytes,
    *,
    max_pages: int = 6,
    dpi: int = 200,
) -> list[bytes]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PDF 処理に PyMuPDF が必要です。") from exc

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("PDF 処理に Pillow が必要です。") from exc

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page_count = min(doc.page_count, max_pages)
        if page_count == 0:
            raise ValueError("PDF にページがありません。")

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pages: list[bytes] = []
        for index in range(page_count):
            pixmap = doc.load_page(index).get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=92, optimize=True)
            pages.append(buffer.getvalue())
        return pages
    finally:
        doc.close()
