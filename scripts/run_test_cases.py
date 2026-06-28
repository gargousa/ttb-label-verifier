import requests
import sys
import argparse
import time
import urllib3


URL_LOCAL = "http://127.0.0.1:8000/verify"
URL_RENDER = "https://ttb-label-verifier.onrender.com/verify"

#Choose the Testing URL based
URL=URL_RENDER

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


def run_test_case(test_case, url, timeout_seconds, verify_ssl, retries):
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
        response = None
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    url,
                    data=data,
                    files=files,
                    timeout=timeout_seconds,
                    verify=verify_ssl,
                )
                break
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < retries:
                    print(f"Retrying ({attempt}/{retries - 1}) after request error...")
                    time.sleep(2)

        if response is None:
            print(f"❌ Request error: {last_error}")
            return False

    print(f"Input brand: {brand_name}")
    print(f"Input ABV: {abv}")

    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code} for {response.url}")
        body_preview = (response.text or "").strip().replace("\n", " ")[:180]
        if body_preview:
            print(f"   Response: {body_preview}")
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
    parser = argparse.ArgumentParser(description="Run label verification test cases")
    parser.add_argument(
        "--url",
        default=URL,
        help="Verification endpoint URL (default: local API)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Request timeout in seconds (default: 90, useful for Render cold starts)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Number of attempts per test case for transient failures (default: 2)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (only for trusted test environments)",
    )
    args = parser.parse_args()

    verify_ssl = not args.insecure
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print(f"Endpoint: {args.url}")
    print(f"Timeout: {args.timeout}s")
    print(f"Retries: {args.retries}")
    print(f"TLS verify: {verify_ssl}")

    passed = 0
    failed = 0

    print_application_data()

    for case in TEST_CASES:
        if run_test_case(case, args.url, args.timeout, verify_ssl, args.retries):
            passed += 1
        else:
            failed += 1

    print("\n=== SUMMARY ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    # Non-zero exit code makes this script automation-friendly.
    sys.exit(1 if failed else 0)
