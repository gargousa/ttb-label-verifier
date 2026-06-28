import requests
import sys

URL = "http://127.0.0.1:8000/verify"

TEST_IMAGE = "tests/images/test_label_stb.jpg"
APPLICATION_TEXT_FILE = "tests/data/label_text.txt"

TEST_CASES = [
    {
        "name": "LABEL: EXACT MATCH",
        "file": "tests/data/test_label_stb_exact.txt",
        "expected": {
            "brand_name": "pass",
            "abv": "pass"
        }
    },
    {
        "name": "LABEL: FUZZY MATCH",
        "file": "tests/data/test_label_stb_fuzzy.txt",
        "expected": {
            "brand_name": "warning",
            "abv": "pass"
        }
    },
    {
        "name": "LABEL: FAIL CASE",
        "file": "tests/data/test_label_stb_fail.txt",
        "expected": {
            "brand_name": "fail",
            "abv": "pass"
        }
    }
]


def run_test_case(test_case):
    print(f"\n=== {test_case['name']} ===")

    with open(test_case["file"]) as f:
        lines = f.read().strip().split("\n")

    brand_name = lines[0]
    abv = lines[1]

    data = {
        "brand_name": brand_name,
        "abv": abv
    }

    with open(TEST_IMAGE, "rb") as image_file:
        files = {
            "file": ("test.jpg", image_file, "image/jpeg")
        }
        response = requests.post(URL, data=data, files=files)

    print(f"Input brand: {brand_name}")
    print(f"Input ABV: {abv}")

    if response.status_code != 200:
        print("❌ Request failed:", response.status_code)
        return False

    result = response.json()
    actual_status_by_field = {}

    for r in result["results"]:
        print(f"{r['field']}: {r['status']} ({r.get('score', '-')})")
        actual_status_by_field[r["field"]] = r["status"]

    expected = test_case["expected"]
    mismatches = []
    for field, expected_status in expected.items():
        actual_status = actual_status_by_field.get(field)
        if actual_status != expected_status:
            mismatches.append(
                f"{field} expected '{expected_status}' but got '{actual_status}'"
            )

    if mismatches:
        print("❌ FAILED")
        for mismatch in mismatches:
            print("   -", mismatch)
        return False

    print("✅ PASSED")
    return True


def print_application_data():
    print("=== APPLICATION DATA ===")
    try:
        with open(APPLICATION_TEXT_FILE, encoding="utf-8") as f:
            print(f.read().strip())
    except FileNotFoundError:
        print(f"Application text file not found: {APPLICATION_TEXT_FILE}")
    print("======================================")


if __name__ == "__main__":
    passed = 0
    failed = 0

    print_application_data()

    for case in TEST_CASES:
        if run_test_case(case):
            passed += 1
        else:
            failed += 1

    print("\n=== SUMMARY ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    # Non-zero exit code makes this script automation-friendly.
    sys.exit(1 if failed else 0)
