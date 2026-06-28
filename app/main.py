from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os

try:
    from app.validation import validate_fields
except ModuleNotFoundError:
    from validation import validate_fields

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

print(f"Running FastAPI server. Upload directory: {UPLOAD_DIR}      ")

@app.get("/")
def root():
    return {"message": "Alcohol Label Verification API is running"}


@app.post("/verify")
async def verify_label(
    brand_name: str = Form(...),
    abv: str = Form(...),
    file: UploadFile = File(...)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # --- Placeholder OCR (replace later) ---
    with open("tests/data/label_text.txt") as f:
        extracted_text = f.read()

    #validation tests
    results = validate_fields(brand_name, abv, extracted_text)

    return JSONResponse({
        "extracted_text": extracted_text,
        "results": results
    })