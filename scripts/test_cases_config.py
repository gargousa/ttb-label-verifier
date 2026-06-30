TEST_CASES = [
    {
        "name": "EXACT FULL CHECKS",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact.jpg",
        "expected": {
            # OCR can occasionally add/remove punctuation or a trailing character on brand text.
            "brand_name": ["pass", "warning"],
            "class_type": "pass",
            "abv": "pass",
            "net_contents": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "EXACT BRAND / ABV MATCH",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv.jpg",
        "expected": {
            "brand_name": "pass",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "FUZZY BRAND / ABV MATCH",
        "application_data_file": "tests/data/stb_fuzzy_application_data.txt",
        "image_file": "tests/images/stb_fuzzy_brand_abv.jpg",
        "expected": {
            "brand_name": "warning",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "FAIL BRAND",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_fail_brand.jpg",
        "expected": {
            "brand_name": "fail",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "ABV MISMATCH",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv_mismatch.jpg",
        "abv_override": "40% ALC/VOL",
        "expected": {
            "brand_name": "pass",
            "abv": "fail",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "ABV WITHIN TOLERANCE",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv_tol.jpg",
        "abv_override": "44% ALC/VOL",
        "expected": {
            "brand_name": "pass",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "producer_name_address",
            "country_of_origin",
        ],
    },
]
