TEST_CASES = [
    {
        "name": "LABEL: EXACT MATCH",
        "file": "tests/data/test_label_stb_exact.txt",
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
        "file": "tests/data/test_label_stb_fuzzy.txt",
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
        "file": "tests/data/test_label_stb_fail.txt",
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
        "file": "tests/data/test_label_stb_exact.txt",
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
        "file": "tests/data/test_label_stb_exact.txt",
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
