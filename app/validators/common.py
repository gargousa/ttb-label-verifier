import re


def normalize_text(text: str) -> str:
    """Normalize text for OCR-tolerant comparison."""
    normalized = re.sub(r"[^a-z0-9]+", " ", str(text).lower())
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_compact(text: str) -> str:
    """Compact normalization that removes all non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def compact_match(expected_compact: str, extracted_text: str) -> bool:
    """Match compact text only when surrounding chars are non-letters."""
    for line in str(extracted_text).splitlines():
        compact_line = normalize_compact(line)
        if not compact_line:
            continue

        idx = compact_line.find(expected_compact)
        if idx == -1:
            continue

        left = compact_line[:idx]
        right = compact_line[idx + len(expected_compact):]
        if not re.search(r"[a-z]", left + right):
            return True

    return False
