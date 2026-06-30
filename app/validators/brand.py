import re
from rapidfuzz import fuzz

try:
    from app.validators.common import compact_match, normalize_compact, normalize_text
except ModuleNotFoundError:
    from validators.common import compact_match, normalize_compact, normalize_text


def validate_brand(expected_brand: str, extracted_text: str) -> dict:
    extracted_lower = str(extracted_text).lower()
    expected_brand_lower = str(expected_brand).lower()
    brand_match_method = "fuzzy"

    if expected_brand_lower in extracted_lower:
        status = "pass"
        score = 100
        brand_match_method = "exact_substring"
    else:
        expected_brand_normalized = normalize_text(expected_brand)
        extracted_normalized = normalize_text(extracted_text)
        expected_brand_compact = normalize_compact(expected_brand)

        if len(expected_brand_normalized.split()) >= 3 and re.search(
            rf"\b{re.escape(expected_brand_normalized)}\b", extracted_normalized
        ):
            status = "pass"
            score = 100
            brand_match_method = "normalized_phrase"
        elif len(expected_brand_compact) >= 12 and compact_match(expected_brand_compact, extracted_text):
            status = "warning"
            score = 99
            brand_match_method = "compact_normalized"
        else:
            score = int(round(max(
                fuzz.partial_ratio(expected_brand_lower, extracted_lower),
                fuzz.token_sort_ratio(expected_brand_lower, extracted_lower)
            )))

            if score >= 85:
                score = min(score, 99)
                status = "warning"
            else:
                status = "fail"

    return {
        "field": "brand_name",
        "status": status,
        "score": score,
        "match_method": brand_match_method,
    }
