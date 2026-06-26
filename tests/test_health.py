from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] in {"healthy", "degraded"}
    assert body["data"]["database"] in {"connected", "disconnected"}


def test_first_phase_routes_are_documented() -> None:
    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/api/v1/auth/signup" in paths
    assert "/api/v1/catalog/products" in paths
    assert "/api/v1/cart" in paths
    assert "/api/v1/orders" in paths
    assert "/api/v1/admin/dashboard" in paths


def test_not_found_uses_standard_error_response() -> None:
    with TestClient(app) as client:
        response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "Not Found",
        "error": {"code": "http_error", "details": None},
        "data": None,
    }
