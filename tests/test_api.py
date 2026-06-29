from fastapi.testclient import TestClient
import app.main as main

app = main.app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_upload_ui_page_available():
    response = client.get("/ui")
    assert response.status_code == 200
    assert "Label Verification UI" in response.text


def test_checks_endpoint():
    response = client.get("/checks")

    assert response.status_code == 200
    data = response.json()
    assert "supported_checks" in data
    assert isinstance(data["supported_checks"], list)
    assert all("field" in check for check in data["supported_checks"])
    assert all("implemented" in check for check in data["supported_checks"])

    checks_by_field = {check["field"]: check for check in data["supported_checks"]}
    assert checks_by_field["brand_name"]["implemented"] is True
    assert checks_by_field["abv"]["implemented"] is True
    assert checks_by_field["class_type"]["implemented"] is True
    assert checks_by_field["net_contents"]["implemented"] is True
    assert checks_by_field["government_warning"]["implemented"] is False


def test_verify_endpoint(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda _path: "OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey 45% ALC/VOL",
    )

    response = client.post(
        "/verify",
        data={
            "brand_name": "OLD TOM DISTILLERY",
            "abv": "45%",
            "class_type": "Kentucky Straight Bourbon Whiskey",
        },
        files={"file": ("test.jpg", b"fakeimage", "image/jpeg")}
    )

    assert response.status_code == 200

    data = response.json()
    assert "supported_checks" in data
    assert "missing_fields" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert all("field" in result and "status" in result for result in data["results"])
    class_type_result = next(item for item in data["results"] if item["field"] == "class_type")
    assert class_type_result["status"] == "pass"
    assert "net_contents" in data["missing_fields"]
    assert "government_warning" in data["missing_fields"]


def test_upload_ui_verify_endpoint(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda _path: "OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey 45% ALC/VOL 750 ML",
    )

    app_data = "\n".join(
        [
            "OLD TOM DISTILLERY",
            "Kentucky Straight Bourbon Whiskey",
            "45% ALC/VOL",
        ]
    )

    response = client.post(
        "/ui/verify",
        files={
            "label_image": ("label.jpg", b"fakeimage", "image/jpeg"),
            "application_data_file": ("application_data.txt", app_data.encode("utf-8"), "text/plain"),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "pass"
    assert "application_data" in data
    assert "results" in data
    assert any(item["field"] == "brand_name" and item["status"] == "pass" for item in data["results"])