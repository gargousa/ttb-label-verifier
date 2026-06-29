from functools import lru_cache
from typing import List

import numpy as np
from PIL import Image, ImageFilter, ImageOps


@lru_cache(maxsize=1)
def _get_reader():
    """Build and cache the EasyOCR reader once per process."""
    try:
        import easyocr
    except ImportError as exc:
        raise RuntimeError(
            "EasyOCR dependency is missing. Install with: pip install easyocr"
        ) from exc

    # Keep language list small for faster startup and better label accuracy.
    return easyocr.Reader(["en"], gpu=False)


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


def _run_ocr_passes(reader, file_path: str) -> List[str]:
    """Run OCR on original and preprocessed variants to improve recall."""
    all_lines: List[str] = []

    # Pass 1: original image.
    original_lines = reader.readtext(
        file_path,
        detail=0,
        paragraph=False,
        decoder="beamsearch",
        beamWidth=7,
        contrast_ths=0.05,
        adjust_contrast=0.7,
    )
    all_lines.extend(str(line) for line in original_lines)

    # Pass 2-3: grayscale/autocontrast variants improve small punctuation and low-contrast text.
    with Image.open(file_path) as image:
        gray = ImageOps.grayscale(image)
        boosted = ImageOps.autocontrast(gray)
        sharpened = boosted.filter(ImageFilter.SHARPEN)
        binary = boosted.point(lambda p: 255 if p > 165 else 0)

        for variant in (sharpened, binary):
            lines = reader.readtext(
                np.array(variant),
                detail=0,
                paragraph=False,
                decoder="beamsearch",
                beamWidth=7,
                contrast_ths=0.03,
                adjust_contrast=0.8,
            )
            all_lines.extend(str(line) for line in lines)

    return _dedupe_lines(all_lines)


def extract_text_from_image(file_path: str) -> str:
    """Extract text from an image file using EasyOCR."""
    if not _is_supported_image(file_path):
        raise ValueError("Unsupported image format. Use JPEG, PNG, or WebP")

    reader = _get_reader()

    try:
        lines = _run_ocr_passes(reader, file_path)
    except Exception as exc:
        message = str(exc)
        if "Could not find a backend to open" in message:
            raise ValueError("Invalid image file. Could not decode uploaded image") from exc
        raise RuntimeError(f"EasyOCR failed for image '{file_path}': {exc}") from exc

    text = "\n".join(line.strip() for line in lines if str(line).strip())
    if not text:
        raise ValueError("Could not read text from image")

    return text
