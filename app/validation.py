from rapidfuzz import fuzz


def validate_fields(expected_brand, expected_abv, extracted_text):
    results = []

    extracted_lower = extracted_text.lower()
    expected_brand_lower = expected_brand.lower()

    # --- Brand Name Matching ---
    if expected_brand_lower in extracted_lower:
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
    if expected_abv in extracted_text:
        abv_status = "pass"
    else:
        abv_status = "fail"

    results.append({
        "field": "abv",
        "status": abv_status
    })

    return results