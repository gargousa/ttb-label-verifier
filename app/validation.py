try:
    from app.validators.abv import (
        compute_abv_score,
        normalize_abv_percent,
        normalize_expected_abv,
        normalize_proof,
        validate_abv,
    )
    from app.validators.brand import validate_brand
    from app.validators.class_type import validate_class_type
    from app.validators.common import compact_match as compact_brand_match
    from app.validators.common import normalize_compact as normalize_brand_compact
    from app.validators.common import normalize_text as normalize_brand_text
    from app.validators.net_contents import normalize_net_contents, validate_net_contents
except ModuleNotFoundError:
    from validators.abv import (
        compute_abv_score,
        normalize_abv_percent,
        normalize_expected_abv,
        normalize_proof,
        validate_abv,
    )
    from validators.brand import validate_brand
    from validators.class_type import validate_class_type
    from validators.common import compact_match as compact_brand_match
    from validators.common import normalize_compact as normalize_brand_compact
    from validators.common import normalize_text as normalize_brand_text
    from validators.net_contents import normalize_net_contents, validate_net_contents


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

def validate_fields(
    expected_brand,
    expected_abv,
    extracted_text,
    expected_class_type=None,
):
    results = [
        validate_brand(expected_brand, extracted_text),
        validate_abv(expected_abv, extracted_text),
        validate_class_type(expected_class_type, extracted_text),
        validate_net_contents(extracted_text),
    ]
    return results