# ttb-label-verifier
TTB Label Verification Take-Home Submission

## Submission Notes

This repository contains a standalone label verification app for the take-home.

- Deployed app: https://ttb-label-verifier-edgk.onrender.com/
- Local run: FastAPI app with browser UIs for verification and test review
- Testing: pytest-based automated checks plus a browser test runner UI

## What's Included

- Upload-based label verification UI
- Live test runner UI with streaming case results
- Deterministic validation for brand, class/type, ABV, and net contents
- Local OCR and per-check missing-items guidance

## Test Data and Images

The repository includes sample assets for local testing and review:

- `data/` contains the text fixtures used by the test runner and validation examples.
- `images/` contains sample label images for OCR and verification testing.
- `uploads/` is used as the local working folder for uploaded files during app runs.

## Overview

The app compares application data to label text using a local OCR pipeline and deterministic validation rules.

- FastAPI serves the API and browser UIs.
- RapidOCR extracts text from uploaded label images.
- Dedicated validation modules evaluate the supported checks.
- The test runner UI exercises the same backend logic used by the upload verification flow.

## High-Level Architecture

The flow is:

Reviewer uses the browser UI -> FastAPI endpoints -> local OCR -> validation modules -> per-check results and missing-items advice -> back to the UI.

## How to Review

The fastest way to evaluate the app is:

1. Open the deployed app and use the upload verification UI at `/ui`.
2. Open the test runner UI at `/tests/ui` to see the built-in cases and live case-by-case results.
3. Run `pytest` locally if you want to confirm the automated coverage.

What to expect:

- Core checks are deterministic and run locally.
- The UI shows the extracted label text, per-check outcomes, and concise missing-items guidance.
- Missing roadmap checks are intentionally left out of scope.

## Scope

This app covers the core verification flow and a focused subset of label checks.

Implemented checks (current):

- brand_name
- class_type
- abv
- net_contents

Not implemented yet (planned for later phases):

- government_warning
- producer_name_address
- country_of_origin

Implemented checks return pass/warning/fail results with scores, and the remaining checks are surfaced as missing until their validation logic is added.

## Assumptions and Limitations

- Application data for the upload UI is expected to be UTF-8 text with brand name, class/type, and ABV on separate lines.
- The app is intentionally local-first and does not depend on external AI or cloud services during verification.
- The missing checks listed in the roadmap remain out of scope.

## Roadmap

Future work, in order:

1. government_warning
2. producer_name_address
3. country_of_origin

Each roadmap item will be added with:

- OCR-tolerant detection logic
- pass/warning/fail + score output
- API coverage tests
- test-runner case expectations updates

## Deployment

The app is deployed on Render for evaluation. OCR and validation run locally in the app process, so the solution does not depend on outbound network access. The free-tier deployment may incur a 30–60 second cold start after inactivity.

## UI Endpoints

Three browser UIs are available:

- Index UI (landing page): `/index`
	- Local: `http://127.0.0.1:8000/index`
	- Render: `https://ttb-label-verifier-edgk.onrender.com/index`

- Test runner UI: `/tests/ui`
	- Local: `http://127.0.0.1:8000/tests/ui`
	- Render: `https://ttb-label-verifier-edgk.onrender.com/tests/ui`

- Upload verification UI: `/ui`
	- Local: `http://127.0.0.1:8000/ui`
	- Render: `https://ttb-label-verifier-edgk.onrender.com/ui`


## Setup and Testing

Run the app and tests locally:

	python -m venv .venv
	.venv\Scripts\Activate.ps1
	python -m pip install -r requirements.txt
	python -m pytest -v

To run the app manually:

	python -m uvicorn app.main:app --reload

Note: the application does not execute the test suite when the API starts.
Tests are run separately with pytest (or automatically in CI on push/PR).

Testing evidence is recorded in [Testing_Evidence.pdf](Testing_Evidence.pdf).

## OCR

OCR is handled locally with RapidOCR (ONNX Runtime) to avoid system-level dependencies such as Tesseract.

RapidOCR can be slower on large images, and the Render free tier can add performance and memory constraints during OCR runs. Those limits would be reduced in a less restricted environment with more CPU and memory headroom.

If OCR cannot detect text from an uploaded image, the API returns HTTP 400. 
If OCR dependencies are missing or OCR processing fails, the API returns HTTP 500.
