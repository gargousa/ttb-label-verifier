from app.validation import validate_fields


def test_full_match():
    extracted = "OLD TOM DISTILLERY 45% ALC/VOL"
    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    assert result[0]["status"] == "pass"
    assert result[1]["status"] == "pass"


def test_brand_case_insensitive():
    extracted = "Stone's Throw 45% ALC/VOL"
    result = validate_fields("STONE'S THROW", "45%", extracted)

    assert result[0]["status"] == "pass"
    assert result[0]["match_method"] == "exact_substring"


def test_abv_mismatch():
    extracted = "OLD TOM DISTILLERY 40% ALC/VOL"
    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    assert result[1]["status"] == "fail"


def test_brand_missing():
    extracted = "RANDOM LABEL 45% ALC/VOL"
    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    assert result[0]["status"] == "fail"

def test_realistic_label_case():
    extracted = """
    OLD TOM DISTILLERY
    Kentucky Straight Bourbon Whiskey
    45% ALC/VOL
    750 ML
    """

    result = validate_fields(
        "OLD TOM DISTILLERY",
        "45%",
        extracted,
        expected_class_type="Kentucky Straight Bourbon Whiskey",
    )

    assert all(r["status"] == "pass" for r in result)    

def test_brand_fuzzy_match_warning():
    extracted = "Stones Throw Bourbon 45%"
    result = validate_fields("STONE'S THROW", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["score"] >= 85
    assert result[0]["score"] < 100
    assert result[0]["match_method"] == "fuzzy"


def test_brand_fuzzy_match_warning_for_distillery_case():
    extracted = "Stones Throw Distillery 90PROOF 750ML"
    result = validate_fields("STONE'S THROW DISTILLERYY", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["score"] < 100


def test_brand_compact_match_warn_for_collapsed_spaces():
    extracted = "STONE'STHROWDISTILLERY 45%"
    result = validate_fields("STONE'S THROW DISTILLERY", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["match_method"] == "compact_normalized"


def test_brand_extra_letter_falls_through_to_fuzzy_not_compact():
    extracted = "STONE'STHROWDISTILLERYY 45%"
    result = validate_fields("STONE'S THROW DISTILLERY", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["match_method"] == "fuzzy"


def test_abv_exact_percent():
    extracted = "45% ALC/VOL"
    result = validate_fields("X", "45%", extracted)

    assert result[1]["status"] == "pass"
    assert isinstance(result[1]["score"], int)
    assert result[1]["score"] == 100


def test_abv_proof_conversion():
    extracted = "90 PROOF"
    result = validate_fields("X", "45%", extracted)

    assert result[1]["status"] == "pass"


def test_abv_expected_proof_matches_percent_extracted():
    extracted = "45% ALC/VOL"
    result = validate_fields("X", "90 PROOF", extracted)

    assert result[1]["status"] == "pass"


def test_abv_mismatch():
    extracted = "40% ALC/VOL"
    result = validate_fields("X", "45%", extracted)

    assert result[1]["status"] == "fail"


def test_net_contents_detected_pass():
    extracted = "OLD TOM DISTILLERY 45% ALC/VOL 750 ML"
    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    net = next(item for item in result if item["field"] == "net_contents")
    assert net["status"] == "pass"
    assert net["score"] == 100
    assert net["detected"] == "750 ML"


def test_net_contents_missing_fails():
    extracted = "OLD TOM DISTILLERY 45% ALC/VOL"
    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    net = next(item for item in result if item["field"] == "net_contents")
    assert net["status"] == "fail"
    assert net["score"] == 0
    assert net["detected"] is None


def test_class_type_exact_match_passes():
    extracted = "Kentucky Straight Bourbon Whiskey"
    result = validate_fields("X", "45%", extracted, expected_class_type="Kentucky Straight Bourbon Whiskey")

    class_type = next(item for item in result if item["field"] == "class_type")
    assert class_type["status"] == "pass"
    assert class_type["score"] == 100


def test_class_type_compact_match_passes_for_collapsed_spacing():
    extracted = "Kentucky StraightBourbon Whiskey"
    result = validate_fields("X", "45%", extracted, expected_class_type="Kentucky Straight Bourbon Whiskey")

    class_type = next(item for item in result if item["field"] == "class_type")
    assert class_type["status"] == "pass"
    assert class_type["match_method"] == "compact_normalized"


def test_class_type_fuzzy_match_warns():
    extracted = "Kentucky Straight Bourbon Whsky"
    result = validate_fields("X", "45%", extracted, expected_class_type="Kentucky Straight Bourbon Whiskey")

    class_type = next(item for item in result if item["field"] == "class_type")
    assert class_type["status"] == "warning"
    assert class_type["score"] < 100


def test_class_type_missing_fails():
    extracted = "OLD TOM DISTILLERY 45% ALC/VOL"
    result = validate_fields("X", "45%", extracted, expected_class_type="Kentucky Straight Bourbon Whiskey")

    class_type = next(item for item in result if item["field"] == "class_type")
    assert class_type["status"] == "fail"
    assert class_type["score"] < 85