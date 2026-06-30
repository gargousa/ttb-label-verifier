import re


def normalize_abv_percent(text: str):
    """Extract ABV % from text (e.g. '45% ALC/VOL')."""
    match = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%", str(text))
    if match:
        return float(match.group(1))
    return None


def normalize_proof(text: str):
    """Extract proof and convert to ABV (proof / 2)."""
    match = re.search(r"(\d{2,3})\s*proof", str(text).lower())
    if match:
        return float(match.group(1)) / 2
    return None


def normalize_expected_abv(text: str):
    percent = normalize_abv_percent(text)
    if percent is not None:
        return percent
    return normalize_proof(text)


def compute_abv_score(expected_val, detected_val):
    if expected_val is None or detected_val is None:
        return 0, None

    delta = abs(detected_val - expected_val)
    score = max(0, int(round(100 - (delta * 25))))
    return score, round(delta, 4)


def validate_abv(expected_abv: str, extracted_text: str) -> dict:
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

    return {
        "field": "abv",
        "status": "pass" if abv_match else "fail",
        "score": abv_score,
        "expected": expected_val,
        "detected_percent": extracted_percent,
        "detected_proof": extracted_proof,
        "detected_source": detected_source,
        "delta": abv_delta,
        "match_method": detected_source or "not_detected",
    }
