from pathlib import Path
from typing import Any, Dict, List

from app.ocr import extract_text_from_image
from app.validation import get_missing_fields, validate_fields
from scripts.test_cases_config import TEST_CASES


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_case_lines(file_path: Path) -> list[str]:
    return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_application_inputs(case: Dict[str, Any], repo_root: Path) -> tuple[str, str, str, str]:
    application_file = repo_root / case.get("application_data_file", "tests/data/application_data.txt")
    lines = _read_case_lines(application_file)
    brand_name = lines[0]
    class_type = lines[1] if len(lines) > 1 else ""
    abv = lines[2] if len(lines) > 2 else ""
    return brand_name, class_type, abv, "\n".join(lines)


def _resolve_case_image_path(case: Dict[str, Any], repo_root: Path, default_image_path: str | None) -> Path:
    image_file = case.get("image_file") or default_image_path or "tests/images/test_label_stb.jpg"
    return repo_root / image_file


def _expected_status_values(expected_status: Any) -> list[str]:
    if isinstance(expected_status, (list, tuple, set)):
        return [str(item).strip().lower() for item in expected_status if str(item).strip()]
    if expected_status is None:
        return []
    return [str(expected_status).strip().lower()]


def _build_missing_items_advice(extracted_text: str) -> list[dict[str, str]]:
    text = str(extracted_text or "").lower()

    has_gov_warning = (
        "government warning" in text
        or "surgeon general" in text
        or "pregnancy" in text and "alcohol" in text
    )

    has_producer_address = (
        "distilled by" in text
        or "bottled by" in text
        or "produced by" in text
        or "llc" in text
        or "inc" in text
        or "street" in text
        or "st " in text
        or " road" in text
        or " rd" in text
    )

    return [
        {"label": "Gov Warning", "status": "Check" if has_gov_warning else "Missing"},
        {"label": "Producer Address", "status": "Check" if has_producer_address else "Missing"},
        {"label": "Origin", "status": "Check"},
    ]


def _run_single_case(
    case: Dict[str, Any],
    repo_root: Path,
    image_path: str | None,
    extracted_text_cache: Dict[Path, str],
) -> Dict[str, Any]:
    application_brand_name, application_class_type, application_abv, application_data_text = _load_application_inputs(case, repo_root)
    resolved_image = _resolve_case_image_path(case, repo_root, image_path)

    if not resolved_image.exists():
        raise RuntimeError(f"Image not found: {resolved_image}")

    if resolved_image not in extracted_text_cache:
        try:
            extracted_text_cache[resolved_image] = extract_text_from_image(str(resolved_image))
        except Exception as exc:
            raise RuntimeError(f"OCR failed for {resolved_image}: {exc}") from exc

    extracted_text = extracted_text_cache[resolved_image]

    results = validate_fields(
        application_brand_name,
        application_abv,
        extracted_text,
        expected_class_type=application_class_type,
    )
    actual_status_by_field = {item["field"]: item["status"] for item in results}

    expected = case["expected"]
    mismatches: List[str] = []
    for field, expected_status in expected.items():
        actual_status = actual_status_by_field.get(field)
        acceptable_statuses = _expected_status_values(expected_status)
        if actual_status not in acceptable_statuses:
            expected_display = " or ".join(f"'{status}'" for status in acceptable_statuses) if acceptable_statuses else "<none>"
            mismatches.append(
                f"{field} expected {expected_display} but got '{actual_status}'"
            )

    expected_missing = case.get("expected_missing_failures", [])
    actual_missing = set(get_missing_fields(results))
    for missing_field in expected_missing:
        if missing_field not in actual_missing:
            mismatches.append(
                f"{missing_field} expected missing/fail but was not reported in missing_fields"
            )

    passed_case = len(mismatches) == 0

    return {
        "name": case["name"],
        "input": {"brand_name": application_brand_name, "abv": application_abv},
        "application_data": {
            "brand_name": application_brand_name,
            "class_type": application_class_type,
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
                "match_method": item.get("match_method"),
            }
            for item in results
        ],
        "missing_items_advice": _build_missing_items_advice(extracted_text),
        "missing_fields": sorted(actual_missing),
        "mismatches": mismatches,
        "passed": passed_case,
    }


def iter_local_test_cases(image_path: str | None = None):
    root = _repo_root()
    extracted_text_cache: Dict[Path, str] = {}

    passed = 0
    failed = 0
    total = len(TEST_CASES)

    for index, case in enumerate(TEST_CASES, start=1):
        try:
            case_result = _run_single_case(case, root, image_path, extracted_text_cache)
        except Exception as exc:
            yield {
                "type": "run_error",
                "ok": False,
                "error": str(exc),
                "case_name": case.get("name"),
                "index": index,
                "total": total,
                "passed": passed,
                "failed": failed,
            }
            return

        if case_result["passed"]:
            passed += 1
        else:
            failed += 1

        yield {
            "type": "case",
            "ok": True,
            "case": case_result,
            "index": index,
            "total": total,
            "passed": passed,
            "failed": failed,
        }

    yield {
        "type": "done",
        "ok": True,
        "passed": passed,
        "failed": failed,
        "total": total,
    }


def run_local_test_cases(image_path: str | None = None) -> Dict[str, Any]:
    root = _repo_root()
    default_image = root / (image_path or "tests/images/test_label_stb.jpg")
    case_results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for event in iter_local_test_cases(image_path=image_path):
        event_type = event.get("type")
        if event_type == "run_error":
            return {
                "ok": False,
                "error": event.get("error", "Unknown test-runner error"),
                "cases": [],
                "passed": 0,
                "failed": 0,
            }

        if event_type == "case":
            case_results.append(event["case"])
            passed = event.get("passed", passed)
            failed = event.get("failed", failed)

        if event_type == "done":
            passed = event.get("passed", passed)
            failed = event.get("failed", failed)

    return {
        "ok": True,
        "image_path": str(default_image),
        "cases": case_results,
        "passed": passed,
        "failed": failed,
    }
