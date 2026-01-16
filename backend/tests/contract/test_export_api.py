import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@pytest.mark.skip(reason="Endpoint not implemented yet")
def test_export_transactions_csv_success():
    response = client.get("/api/v1/export/transactions?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.skip(reason="Endpoint not implemented yet")
def test_export_transactions_html_success():
    response = client.get("/api/v1/export/transactions?format=html")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@pytest.mark.skip(reason="Endpoint not implemented yet")
def test_export_transactions_invalid_format():
    response = client.get("/api/v1/export/transactions?format=pdf")
    assert response.status_code == 422


@pytest.mark.skip(reason="Endpoint not implemented yet")
def test_export_transactions_invalid_date_range():
    response = client.get(
        "/api/v1/export/transactions?start_date=2024-02-01&end_date=2024-01-01&format=csv"
    )
    assert response.status_code == 422
