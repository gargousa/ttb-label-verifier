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

The prototype uses EasyOCR to avoid system-level dependencies (e.g., Tesseract binaries),
making it easier to deploy in restricted environments.

While EasyOCR is slightly slower than Tesseract, the performance is acceptable for
a prototype and provides better robustness against real-world label variations.
The /verify endpoint uses EasyOCR to scan uploaded label images.

Memory mode configuration:

	OCR_MODE=lite     # default, single-pass OCR with lower memory footprint
	OCR_MODE=accurate # optional, multi-pass OCR with preprocessing (higher memory)

For Render free-tier services, keep OCR_MODE=lite to avoid out-of-memory restarts.

Install dependencies:

	python -m pip install -r requirements.txt

If OCR cannot detect text from an uploaded image, the API returns HTTP 400.
If OCR dependencies are missing or OCR processing fails, the API returns HTTP 500.
