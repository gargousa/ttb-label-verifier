TEST_CASES = [
    {
        "name": "LABEL: EXACT MATCH",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv.jpg",
        "expected": {
            "brand_name": "pass",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "class_type",
            "net_contents",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "LABEL: FUZZY MATCH",
        "application_data_file": "tests/data/stb_fuzzy_application_data.txt",
        "image_file": "tests/images/stb_fuzzy_brand_abv.jpg",
        "expected": {
            "brand_name": "pass",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "class_type",
            "net_contents",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "LABEL: FAIL CASE",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_fail_brand.jpg",
        "expected": {
            "brand_name": "fail",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "class_type",
            "net_contents",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "LABEL: ABV MISMATCH",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv_mismatch.jpg",
        "abv_override": "40% ALC/VOL",
        "expected": {
            "brand_name": "pass",
            "abv": "fail",
        },
        "expected_missing_failures": [
            "government_warning",
            "class_type",
            "net_contents",
            "producer_name_address",
            "country_of_origin",
        ],
    },
    {
        "name": "LABEL: ABV WITHIN TOLERANCE",
        "application_data_file": "tests/data/application_data.txt",
        "image_file": "tests/images/stb_exact_brand_abv_tol.jpg",
        "abv_override": "44% ALC/VOL",
        "expected": {
            "brand_name": "pass",
            "abv": "pass",
        },
        "expected_missing_failures": [
            "government_warning",
            "class_type",
            "net_contents",
            "producer_name_address",
            "country_of_origin",
        ],
    },
]
