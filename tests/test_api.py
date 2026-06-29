from fastapi.testclient import TestClient
import app.main as main

app = main.app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


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
    assert checks_by_field["government_warning"]["implemented"] is False


def test_verify_endpoint(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda _path: "OLD TOM DISTILLERY 45% ALC/VOL",
    )

    response = client.post(
        "/verify",
        data={
            "brand_name": "OLD TOM DISTILLERY",
            "abv": "45%"
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
    assert "government_warning" in data["missing_fields"]
    assert "class_type" in data["missing_fields"]