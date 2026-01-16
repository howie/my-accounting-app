from fastapi.testclient import TestClient


def test_export_transactions_csv_success(client: TestClient):
    response = client.get("/api/v1/export/transactions?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


def test_export_transactions_html_success(client: TestClient):
    response = client.get("/api/v1/export/transactions?format=html")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_export_transactions_invalid_format(client: TestClient):
    response = client.get("/api/v1/export/transactions?format=pdf")
    assert response.status_code == 422


def test_export_transactions_invalid_date_range(client: TestClient):
    response = client.get(
        "/api/v1/export/transactions?start_date=2024-02-01&end_date=2024-01-01&format=csv"
    )
    assert response.status_code == 422
