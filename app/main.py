from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    extracted_text = "OLD TOM DISTILLERY 45% ALC/VOL 750 ML"

    results = []

    if brand_name.lower() in extracted_text.lower():
        results.append({"field": "brand_name", "status": "pass"})
    else:
        results.append({"field": "brand_name", "status": "fail"})

    if abv in extracted_text:
        results.append({"field": "abv", "status": "pass"})
    else:
        results.append({"field": "abv", "status": "fail"})

    return JSONResponse({
        "extracted_text": extracted_text,
        "results": results
    })