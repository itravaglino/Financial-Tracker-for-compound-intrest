import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_data import demo_fundamentals, demo_quote


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "demo_mode" in data


def test_register_and_login():
    response = client.post(
        "/api/auth/register",
        json={"username": "pytest_user", "email": "pytest@example.com", "password": "secret123"},
    )
    assert response.status_code == 201

    login = client.post(
        "/api/auth/login",
        data={"username": "pytest_user", "password": "secret123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_demo_quote():
    quote = demo_quote("AAPL")
    assert quote["symbol"] == "AAPL"
    assert quote["price"] > 0
    assert quote["demo_mode"] is True


def test_demo_fundamentals():
    fund = demo_fundamentals("MSFT")
    assert fund["symbol"] == "MSFT"
    assert fund["pe_ratio"] is not None


def test_quote_endpoint_authenticated():
    client.post(
        "/api/auth/register",
        json={"username": "quote_user", "email": "quote@example.com", "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        data={"username": "quote_user", "password": "secret123"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/analysis/quote/AAPL",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] > 0


def test_import_yahoo_portfolio():
    client.post(
        "/api/auth/register",
        json={"username": "import_user", "email": "import@example.com", "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        data={"username": "import_user", "password": "secret123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/portfolio/import-yahoo",
        headers={"Authorization": f"Bearer {token}"},
        json={"symbols": ["AAPL", "MSFT"], "portfolio_name": "Test"},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["holdings"]) == 2
