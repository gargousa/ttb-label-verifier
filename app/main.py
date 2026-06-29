from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import shutil
import os
from pathlib import Path

try:
    from app.validation import validate_fields, get_supported_checks, get_missing_fields
    from app.ocr import extract_text_from_image
    from app.test_runner import run_local_test_cases
except ModuleNotFoundError:
    from validation import validate_fields, get_supported_checks, get_missing_fields
    from ocr import extract_text_from_image
    from test_runner import run_local_test_cases

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
TEST_UI_FILE = Path(__file__).resolve().parent / "templates" / "tests_ui.html"
VERIFY_UI_FILE = Path(__file__).resolve().parent / "templates" / "verify_ui.html"

print(f"Running FastAPI server. Upload directory: {UPLOAD_DIR}      ")


def _compute_overall_status(results: list[dict]) -> str:
    statuses = {str(item.get("status", "")).lower() for item in results}
    if "fail" in statuses:
        return "fail"
    if "warning" in statuses:
        return "warning"
    return "pass"


def _parse_application_data_text(raw_text: str) -> dict[str, str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if len(lines) < 3:
        raise HTTPException(
            status_code=400,
            detail="Application data file must include at least 3 non-empty lines: brand_name, class_type, abv.",
        )

    return {
        "brand_name": lines[0],
        "class_type": lines[1],
        "abv": lines[2],
        "raw_text": "\n".join(lines),
    }

@app.get("/")
def root():
    return {"message": "Alcohol Label Verification API is running"}


@app.get("/verify")
def verify_info():
    return {"message": "Use POST method with form-data to verify labels"}


@app.get("/checks")
def checks_info():
    return {"supported_checks": get_supported_checks()}


@app.get("/tests/ui", response_class=HTMLResponse)
def tests_ui():
    return TEST_UI_FILE.read_text(encoding="utf-8")


@app.get("/ui", response_class=HTMLResponse)
def verify_ui():
    return VERIFY_UI_FILE.read_text(encoding="utf-8")


@app.post("/tests/ui/run")
def tests_ui_run(payload: dict | None = None):
    payload = payload or {}
    image_path = payload.get("image_path")
    return run_local_test_cases(image_path=image_path)


@app.post("/ui/verify")
async def verify_ui_run(
    label_image: UploadFile = File(...),
    application_data_file: UploadFile = File(...),
):
    try:
        application_data_bytes = await application_data_file.read()
        application_data_text = application_data_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Application data file must be UTF-8 text.") from exc

    parsed_application_data = _parse_application_data_text(application_data_text)

    file_path = os.path.join(UPLOAD_DIR, label_image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(label_image.file, buffer)

    try:
        extracted_text = extract_text_from_image(file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    results = validate_fields(
        parsed_application_data["brand_name"],
        parsed_application_data["abv"],
        extracted_text,
        expected_class_type=parsed_application_data["class_type"],
    )
    missing_fields = get_missing_fields(results)

    return JSONResponse(
        {
            "application_data": parsed_application_data,
            "extracted_text": extracted_text,
            "results": results,
            "missing_fields": missing_fields,
            "overall_status": _compute_overall_status(results),
        }
    )

@app.post("/verify")
async def verify_label(
    brand_name: str = Form(...),
    abv: str = Form(...),
    class_type: str | None = Form(None),
    file: UploadFile = File(...)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extracted_text = extract_text_from_image(file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    #validation tests
    results = validate_fields(brand_name, abv, extracted_text, expected_class_type=class_type)
    missing_fields = get_missing_fields(results)

    return JSONResponse({
        "extracted_text": extracted_text,
        "supported_checks": get_supported_checks(),
        "missing_fields": missing_fields,
        "results": results,
    })