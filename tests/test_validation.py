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

    result = validate_fields("OLD TOM DISTILLERY", "45%", extracted)

    assert all(r["status"] == "pass" for r in result)    

def test_brand_fuzzy_match_warning():
    extracted = "Stones Throw Bourbon 45%"
    result = validate_fields("STONE'S THROW", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["score"] >= 85
    assert result[0]["score"] < 100


def test_brand_fuzzy_match_warning_for_distillery_case():
    extracted = "Stones Throw Distillery 90PROOF 750ML"
    result = validate_fields("STONE'S THROW DISTILLERYY", "45%", extracted)

    assert result[0]["status"] == "warning"
    assert result[0]["score"] < 100


def test_brand_compact_match_pass_for_collapsed_spaces():
    extracted = "STONE'STHROWDISTILLERY 45%"
    result = validate_fields("STONE'S THROW DISTILLERY", "45%", extracted)

    assert result[0]["status"] == "pass"

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