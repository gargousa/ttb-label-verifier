from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_verify_endpoint():
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
    assert "results" in data
    assert isinstance(data["results"], list)
    assert all("field" in result and "status" in result for result in data["results"])