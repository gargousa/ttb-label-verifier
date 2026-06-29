# ttb-label-verifier
AI-Powered Alcohol Label Verification App

## Deployment

This application is deployed on Render for ease of evaluation.

All OCR and validation logic runs locally within the application process and does not require outbound network access. This allows the solution to be deployed in restricted environments where outbound traffic is blocked.

Note: The free-tier deployment may incur a 30–60 second cold start after inactivity.


## Testing

Run tests locally:

	python -m venv .venv
	.venv\Scripts\Activate.ps1
	python -m pip install -r requirements.txt
	python -m pytest -v

Note: the application does not execute the test suite when the API starts.
Tests are run separately with pytest (or automatically in CI on push/PR).

## OCR
OCR Design Choice:

The active OCR implementation uses RapidOCR (ONNX Runtime) to avoid system-level
dependencies (e.g., Tesseract binaries) and reduce memory usage on constrained deployments.

EasyOCR is still listed as a dependency for compatibility experiments, but it is not called
by the current OCR pipeline.

The /verify endpoint uses RapidOCR to scan uploaded label images.

Memory mode configuration:

	OCR_MAX_SIDE=1024 # optional, downscale long edge before OCR to reduce peak memory

For Render free-tier services, lower OCR_MAX_SIDE (for example 896 or 768) if memory pressure continues.

Install dependencies:

	python -m pip install -r requirements.txt

If OCR cannot detect text from an uploaded image, the API returns HTTP 400.
If OCR dependencies are missing or OCR processing fails, the API returns HTTP 500.
