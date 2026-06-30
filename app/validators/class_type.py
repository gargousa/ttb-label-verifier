import re
from rapidfuzz import fuzz

try:
    from app.validators.common import normalize_compact, normalize_text
except ModuleNotFoundError:
    from validators.common import normalize_compact, normalize_text


def validate_class_type(expected_class_type: str | None, extracted_text: str) -> dict:
    class_type_expected = (expected_class_type or "").strip()
    class_type_detected = None
    class_type_match_method = "fuzzy"

    if not class_type_expected:
        class_type_status = "fail"
        class_type_score = 0
        class_type_match_method = "no_expected"
    else:
        expected_class_lower = class_type_expected.lower()
        extracted_lower = str(extracted_text).lower()
        expected_class_normalized = normalize_text(class_type_expected)
        extracted_normalized = normalize_text(extracted_text)
        expected_class_compact = normalize_compact(class_type_expected)
        extracted_class_compact = normalize_compact(extracted_text)

        if expected_class_lower in extracted_lower:
            class_type_status = "pass"
            class_type_score = 100
            class_type_detected = class_type_expected
            class_type_match_method = "exact_substring"
        elif re.search(rf"\b{re.escape(expected_class_normalized)}\b", extracted_normalized):
            class_type_status = "pass"
            class_type_score = 100
            class_type_detected = class_type_expected
            class_type_match_method = "normalized_phrase"
        elif len(expected_class_compact) >= 12 and expected_class_compact in extracted_class_compact:
            class_type_status = "pass"
            class_type_score = 100
            class_type_detected = class_type_expected
            class_type_match_method = "compact_normalized"
        else:
            class_type_score = int(round(max(
                fuzz.partial_ratio(expected_class_lower, extracted_lower),
                fuzz.token_sort_ratio(expected_class_lower, extracted_lower)
            )))

            if class_type_score >= 85:
                class_type_score = min(class_type_score, 99)
                class_type_status = "warning"
            else:
                class_type_status = "fail"

    return {
        "field": "class_type",
        "status": class_type_status,
        "score": class_type_score,
        "expected": class_type_expected or None,
        "detected": class_type_detected,
        "match_method": class_type_match_method,
    }
