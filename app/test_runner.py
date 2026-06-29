from pathlib import Path
from typing import Any, Dict, List

from app.ocr import extract_text_from_image
from app.validation import get_missing_fields, validate_fields
from scripts.test_cases_config import TEST_CASES


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_case_inputs(case: Dict[str, Any], repo_root: Path) -> tuple[str, str]:
    case_file = repo_root / case["file"]
    lines = case_file.read_text(encoding="utf-8").strip().split("\n")
    brand_name = lines[0]
    abv = case.get("abv_override", lines[1])
    return brand_name, abv


def run_local_test_cases(image_path: str | None = None) -> Dict[str, Any]:
    root = _repo_root()
    resolved_image = root / (image_path or "tests/images/test_label_stb.jpg")

    if not resolved_image.exists():
        return {
            "ok": False,
            "error": f"Image not found: {resolved_image}",
            "cases": [],
            "passed": 0,
            "failed": 0,
        }

    try:
        extracted_text = extract_text_from_image(str(resolved_image))
    except Exception as exc:
        return {
            "ok": False,
            "error": f"OCR failed: {exc}",
            "cases": [],
            "passed": 0,
            "failed": 0,
        }

    case_results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for case in TEST_CASES:
        brand_name, abv = _load_case_inputs(case, root)

        results = validate_fields(brand_name, abv, extracted_text)
        actual_status_by_field = {item["field"]: item["status"] for item in results}

        expected = case["expected"]
        mismatches: List[str] = []
        for field, expected_status in expected.items():
            actual_status = actual_status_by_field.get(field)
            if actual_status != expected_status:
                mismatches.append(
                    f"{field} expected '{expected_status}' but got '{actual_status}'"
                )

        expected_missing = case.get("expected_missing_failures", [])
        actual_missing = set(get_missing_fields(results))
        for missing_field in expected_missing:
            if missing_field not in actual_missing:
                mismatches.append(
                    f"{missing_field} expected missing/fail but was not reported in missing_fields"
                )

        passed_case = len(mismatches) == 0
        if passed_case:
            passed += 1
        else:
            failed += 1

        case_results.append(
            {
                "name": case["name"],
                "input": {"brand_name": brand_name, "abv": abv},
                "expected": expected,
                "actual": actual_status_by_field,
                "missing_fields": sorted(actual_missing),
                "mismatches": mismatches,
                "passed": passed_case,
            }
        )

    return {
        "ok": True,
        "image_path": str(resolved_image),
        "extracted_text": extracted_text,
        "cases": case_results,
        "passed": passed,
        "failed": failed,
    }
