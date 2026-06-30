import re


def normalize_net_contents(text: str):
    match = re.search(
        r"\b(\d{1,4}(?:\.\d{1,2})?)\s*(ml|l|cl|fl\.?\s*oz)\b",
        str(text),
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    value = match.group(1)
    unit = re.sub(r"\s+", " ", match.group(2).lower().replace(".", "")).strip()
    return f"{value} {unit.upper()}"


def validate_net_contents(extracted_text: str) -> dict:
    detected_net_contents = normalize_net_contents(extracted_text)
    return {
        "field": "net_contents",
        "status": "pass" if detected_net_contents else "fail",
        "score": 100 if detected_net_contents else 0,
        "detected": detected_net_contents,
        "match_method": "regex_detected" if detected_net_contents else "not_detected",
    }
