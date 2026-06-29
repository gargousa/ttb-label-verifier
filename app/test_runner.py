from pathlib import Path
from typing import Any, Dict, List

from app.ocr import extract_text_from_image
from app.validation import get_missing_fields, validate_fields
from scripts.test_cases_config import TEST_CASES


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_case_lines(file_path: Path) -> list[str]:
    return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_application_inputs(case: Dict[str, Any], repo_root: Path) -> tuple[str, str, str]:
    application_file = repo_root / case.get("application_data_file", "tests/data/application_data.txt")
    lines = _read_case_lines(application_file)
    brand_name = lines[0]
    abv = lines[2]
    return brand_name, abv, "\n".join(lines)


def _resolve_case_image_path(case: Dict[str, Any], repo_root: Path, default_image_path: str | None) -> Path:
    image_file = case.get("image_file") or default_image_path or "tests/images/test_label_stb.jpg"
    return repo_root / image_file


def run_local_test_cases(image_path: str | None = None) -> Dict[str, Any]:
    root = _repo_root()
    default_image = root / (image_path or "tests/images/test_label_stb.jpg")

    extracted_text_cache: Dict[Path, str] = {}

    case_results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for case in TEST_CASES:
        application_brand_name, application_abv, application_data_text = _load_application_inputs(case, root)
        resolved_image = _resolve_case_image_path(case, root, image_path)

        if not resolved_image.exists():
            return {
                "ok": False,
                "error": f"Image not found: {resolved_image}",
                "cases": [],
                "passed": 0,
                "failed": 0,
            }

        if resolved_image not in extracted_text_cache:
            try:
                extracted_text_cache[resolved_image] = extract_text_from_image(str(resolved_image))
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"OCR failed for {resolved_image}: {exc}",
                    "cases": [],
                    "passed": 0,
                    "failed": 0,
                }

        extracted_text = extracted_text_cache[resolved_image]

        results = validate_fields(application_brand_name, application_abv, extracted_text)
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
                "input": {"brand_name": application_brand_name, "abv": application_abv},
                "application_data": {
                    "brand_name": application_brand_name,
                    "abv": application_abv,
                },
                "application_data_text": application_data_text,
                "image_path": str(resolved_image),
                "extracted_text": extracted_text,
                "expected": expected,
                "actual": actual_status_by_field,
                "checks": [
                    {
                        "field": item.get("field"),
                        "status": item.get("status"),
                        "score": item.get("score"),
                    }
                    for item in results
                ],
                "missing_fields": sorted(actual_missing),
                "mismatches": mismatches,
                "passed": passed_case,
            }
        )

    return {
        "ok": True,
        "image_path": str(default_image),
        "cases": case_results,
        "passed": passed,
        "failed": failed,
    }
