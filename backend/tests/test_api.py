from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_companies_endpoint():
    with client:
        response = client.get("/companies")
    assert response.status_code == 200
    symbols = {item["symbol"] for item in response.json()["data"]}
    assert {"TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK"}.issubset(symbols)


def test_invalid_symbol():
    with client:
        response = client.get("/summary/NOTREAL")
    assert response.status_code == 404
