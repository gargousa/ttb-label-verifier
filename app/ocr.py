from functools import lru_cache
import os
from typing import List


def _is_supported_image(file_path: str) -> bool:
    """Check if file looks like JPEG, PNG, or WebP by magic bytes."""
    with open(file_path, "rb") as f:
        header = f.read(16)

    is_jpeg = header.startswith(b"\xff\xd8\xff")
    is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    return is_jpeg or is_png or is_webp


def _dedupe_lines(lines: List[str]) -> List[str]:
    """Deduplicate OCR lines while preserving order."""
    deduped: List[str] = []
    seen = set()
    for line in lines:
        value = str(line).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


@lru_cache(maxsize=1)
def _get_rapidocr_engine():
    """Build and cache RapidOCR engine once per process."""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "RapidOCR dependency is missing. Install with: pip install rapidocr-onnxruntime"
        ) from exc

    return RapidOCR()


def _prepare_image_array(file_path: str):
    """Load and downscale image before OCR to lower peak memory usage."""
    import numpy as np
    from PIL import Image, ImageOps

    max_side = int(os.getenv("OCR_MAX_SIDE", "1024"))

    with Image.open(file_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        return np.array(image)


def _extract_lines_from_rapidocr_result(ocr_result) -> List[str]:
    """Extract text lines from RapidOCR raw output."""
    lines: List[str] = []
    if not ocr_result:
        return lines

    for item in ocr_result:
        # Expected shape: [box, text, score]
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            text = item[1]
        elif isinstance(item, dict):
            text = item.get("text")
        else:
            text = None

        if text:
            lines.append(str(text))

    return _dedupe_lines(lines)


def extract_text_from_image(file_path: str) -> str:
    """Extract text from an image file using RapidOCR."""
    if not _is_supported_image(file_path):
        raise ValueError("Unsupported image format. Use JPEG, PNG, or WebP")

    engine = _get_rapidocr_engine()
    image_array = _prepare_image_array(file_path)

    try:
        ocr_result, _ = engine(image_array)
    except Exception as exc:
        message = str(exc)
        if "cannot identify image file" in message.lower() or "Could not find a backend to open" in message:
            raise ValueError("Invalid image file. Could not decode uploaded image") from exc
        raise RuntimeError(f"RapidOCR failed for image '{file_path}': {exc}") from exc

    lines = _extract_lines_from_rapidocr_result(ocr_result)
    text = "\n".join(lines)
    if not text:
        raise ValueError("Could not read text from image")

    return text
