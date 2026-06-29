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

print(f"Running FastAPI server. Upload directory: {UPLOAD_DIR}      ")

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


@app.post("/tests/ui/run")
def tests_ui_run(payload: dict | None = None):
    payload = payload or {}
    image_path = payload.get("image_path")
    return run_local_test_cases(image_path=image_path)

@app.post("/verify")
async def verify_label(
    brand_name: str = Form(...),
    abv: str = Form(...),
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
    results = validate_fields(brand_name, abv, extracted_text)
    missing_fields = get_missing_fields(results)

    return JSONResponse({
        "extracted_text": extracted_text,
        "supported_checks": get_supported_checks(),
        "missing_fields": missing_fields,
        "results": results,
    })