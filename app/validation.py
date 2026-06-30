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
        "implemented": True,
    },
    {
        "field": "net_contents",
        "description": "Checks net contents value and unit formatting",
        "implemented": True,
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

        if field == "class_type" and result.get("status") == "fail":
            missing.append("class_type")

        if field == "net_contents" and result.get("status") == "fail":
            missing.append("net_contents")

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


def normalize_brand_compact(text):
    """Compact normalization that removes all non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def compact_brand_match(expected_compact, extracted_text):
    """Match compact brand only when surrounding chars are non-letters (spacing/punctuation collapse)."""
    for line in extracted_text.splitlines():
        compact_line = normalize_brand_compact(line)
        if not compact_line:
            continue

        idx = compact_line.find(expected_compact)
        if idx == -1:
            continue

        left = compact_line[:idx]
        right = compact_line[idx + len(expected_compact):]
        # Allow only numeric/noise around the compact brand; extra letters should fall through to fuzzy.
        if not re.search(r"[a-z]", left + right):
            return True

    return False


def normalize_net_contents(text):
    """Extract net contents value + unit from OCR text (e.g. 750 ML, 1.75 L)."""
    match = re.search(
        r"\b(\d{1,4}(?:\.\d{1,2})?)\s*(ml|l|cl|fl\.?\s*oz)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    value = match.group(1)
    unit = re.sub(r"\s+", " ", match.group(2).lower().replace(".", "")).strip()
    return f"{value} {unit.upper()}"


def compute_abv_score(expected_val, detected_val):
    """Compute a simple 0-100 confidence score from ABV delta."""
    if expected_val is None or detected_val is None:
        return 0, None

    delta = abs(detected_val - expected_val)
    # 100 at exact match; degrades with larger delta and bottoms at 0.
    score = max(0, int(round(100 - (delta * 25))))
    return score, round(delta, 4)

def validate_fields(expected_brand, expected_abv, extracted_text, expected_class_type=None):
    results = []

    extracted_lower = extracted_text.lower()
    expected_brand_lower = expected_brand.lower()
    brand_match_method = "fuzzy"

    # --- Brand Name Matching ---
    if expected_brand_lower in extracted_lower:
        status = "pass"
        score = 100
        brand_match_method = "exact_substring"
    else:
        expected_brand_normalized = normalize_brand_text(expected_brand)
        extracted_normalized = normalize_brand_text(extracted_text)
        expected_brand_compact = normalize_brand_compact(expected_brand)
        extracted_compact = normalize_brand_compact(extracted_text)

        # OCR often splits punctuation/newlines. Accept normalized exact phrase for longer brands.
        if len(expected_brand_normalized.split()) >= 3 and re.search(
            rf"\b{re.escape(expected_brand_normalized)}\b", extracted_normalized
        ):
            status = "pass"
            score = 100
            brand_match_method = "normalized_phrase"
        elif len(expected_brand_compact) >= 12 and compact_brand_match(expected_brand_compact, extracted_text):
            # OCR may collapse spaces/punctuation for long names (e.g. STONE'STHROWDISTILLERY).
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
                status = "warning"   # close match (case, punctuation, spacing)
            else:
                status = "fail"

    results.append({
        "field": "brand_name",
        "status": status,
        "score": score,
        "match_method": brand_match_method,
    })

    # --- ABV Matching (strict for now) ---
    expected_val = normalize_expected_abv(expected_abv)

    extracted_percent = normalize_abv_percent(extracted_text)
    extracted_proof = normalize_proof(extracted_text)

    abv_match = False
    detected_value = None
    detected_source = None

    if extracted_percent is not None and expected_val is not None:
        detected_value = extracted_percent
        detected_source = "percent"
        if abs(extracted_percent - expected_val) <= 1:
            abv_match = True

    elif extracted_proof is not None and expected_val is not None:
        detected_value = extracted_proof
        detected_source = "proof"
        if abs(extracted_proof - expected_val) <= 1:
            abv_match = True

    abv_score, abv_delta = compute_abv_score(expected_val, detected_value)

    abv_status = "pass" if abv_match else "fail"
    abv_match_method = detected_source or "not_detected"


    results.append({
        "field": "abv",
        "status": abv_status,
        "score": abv_score,
        "expected": expected_val,
        "detected_percent": extracted_percent,
        "detected_proof": extracted_proof,
        "detected_source": detected_source,
        "delta": abv_delta,
        "match_method": abv_match_method,
    })

    # --- Class/Type Matching ---
    class_type_expected = (expected_class_type or "").strip()
    class_type_detected = None
    class_type_match_method = "fuzzy"

    if not class_type_expected:
        class_type_status = "fail"
        class_type_score = 0
        class_type_match_method = "no_expected"
    else:
        expected_class_lower = class_type_expected.lower()
        extracted_lower = extracted_text.lower()
        expected_class_normalized = normalize_brand_text(class_type_expected)
        extracted_normalized = normalize_brand_text(extracted_text)
        expected_class_compact = normalize_brand_compact(class_type_expected)
        extracted_class_compact = normalize_brand_compact(extracted_text)

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

    results.append({
        "field": "class_type",
        "status": class_type_status,
        "score": class_type_score,
        "expected": class_type_expected or None,
        "detected": class_type_detected,
        "match_method": class_type_match_method,
    })

    # --- Net Contents / Volume Matching ---
    detected_net_contents = normalize_net_contents(extracted_text)
    net_contents_status = "pass" if detected_net_contents else "fail"
    net_contents_score = 100 if detected_net_contents else 0

    results.append({
        "field": "net_contents",
        "status": net_contents_status,
        "score": net_contents_score,
        "detected": detected_net_contents,
        "match_method": "regex_detected" if detected_net_contents else "not_detected",
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