from rapidfuzz import fuzz
import re


SUPPORTED_CHECKS = [
    {
        "field": "brand_name",
        "description": "Compares expected brand name against OCR text with exact and fuzzy matching",
        "implemented": True,
    },
    {
        "field": "abv",
        "description": "Compares expected ABV against OCR-detected percent or proof",
        "implemented": True,
    },
    {
        "field": "government_warning",
        "description": "Detects presence of required government health warning statement",
        "implemented": False,
    },
    {
        "field": "class_type",
        "description": "Checks class/type designation against expected value",
        "implemented": False,
    },
    {
        "field": "net_contents",
        "description": "Checks net contents value and unit formatting",
        "implemented": False,
    },
    {
        "field": "producer_name_address",
        "description": "Checks producer or bottler name/address presence",
        "implemented": False,
    },
    {
        "field": "country_of_origin",
        "description": "Checks country of origin for imported products",
        "implemented": False,
    },
]


def get_supported_checks():
    """Return the checks currently supported by the comparison engine."""
    return list(SUPPORTED_CHECKS)


def get_missing_fields(results):
    """Return fields that are missing or not detectable from OCR output."""
    missing = []

    for check in SUPPORTED_CHECKS:
        if not check.get("implemented", False):
            missing.append(check["field"])

    for result in results:
        field = result.get("field")
        if field == "brand_name" and result.get("status") == "fail":
            missing.append("brand_name")

        if field == "abv":
            detected_percent = result.get("detected_percent")
            detected_proof = result.get("detected_proof")
            if detected_percent is None and detected_proof is None:
                missing.append("abv")

    # Remove duplicates while preserving order.
    deduped = []
    seen = set()
    for name in missing:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)
    return deduped


def normalize_brand_text(text):
    """Normalize text for OCR-tolerant brand comparison."""
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", normalized).strip()

def validate_fields(expected_brand, expected_abv, extracted_text):
    results = []

    extracted_lower = extracted_text.lower()
    expected_brand_lower = expected_brand.lower()

    # --- Brand Name Matching ---
    if expected_brand_lower in extracted_lower:
        status = "pass"
        score = 100
    else:
        expected_brand_normalized = normalize_brand_text(expected_brand)
        extracted_normalized = normalize_brand_text(extracted_text)

        # OCR often splits punctuation/newlines. Accept normalized exact phrase for longer brands.
        if len(expected_brand_normalized.split()) >= 3 and re.search(
            rf"\b{re.escape(expected_brand_normalized)}\b", extracted_normalized
        ):
            status = "pass"
            score = 100
        else:
            score = max(
                fuzz.partial_ratio(expected_brand_lower, extracted_lower),
                fuzz.token_sort_ratio(expected_brand_lower, extracted_lower)
            )

            if score >= 85:
                status = "warning"   # close match (case, punctuation, spacing)
            else:
                status = "fail"

    results.append({
        "field": "brand_name",
        "status": status,
        "score": score
    })

    # --- ABV Matching (strict for now) ---
    expected_val = normalize_expected_abv(expected_abv)

    extracted_percent = normalize_abv_percent(extracted_text)
    extracted_proof = normalize_proof(extracted_text)

    abv_match = False

    if extracted_percent is not None and expected_val is not None:
        if abs(extracted_percent - expected_val) <= 1:
            abv_match = True

    elif extracted_proof is not None and expected_val is not None:
        if abs(extracted_proof - expected_val) <= 1:
            abv_match = True

    abv_status = "pass" if abv_match else "fail"


    results.append({
        "field": "abv",
        "status": abv_status,
        "expected": expected_val,
        "detected_percent": extracted_percent,
        "detected_proof": extracted_proof
    })

    return results


def normalize_abv_percent(text):
    """
    Extract ABV % from text (e.g. '45% ALC/VOL').
    Returns float or None.
    """
    match = re.search(r'(\d{1,2}(?:\.\d+)?)\s*%', text)
    if match:
        return float(match.group(1))
    return None


def normalize_expected_abv(text):
    """
    Normalize an expected ABV value from either percent or proof text.
    Returns ABV percent as float or None.
    """
    percent = normalize_abv_percent(text)
    if percent is not None:
        return percent
    return normalize_proof(text)


def normalize_proof(text):
    """
    Extract proof and convert to ABV (proof / 2).
    """
    match = re.search(r'(\d{2,3})\s*proof', text.lower())
    if match:
        return float(match.group(1)) / 2
    return None    