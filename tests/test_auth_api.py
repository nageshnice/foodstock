from fastapi.testclient import TestClient


def test_signup_login_and_protected_api(api_client: TestClient) -> None:
    signup = api_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "customer@example.com",
            "password": "strong-password",
            "confirm_password": "strong-password",
        },
    )
    assert signup.status_code == 201
    token = signup.json()["data"]["access_token"]

    unauthorized = api_client.get("/api/v1/catalog/regions")
    assert unauthorized.status_code == 401

    authorized = api_client.get(
        "/api/v1/catalog/regions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["data"] == []

    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "customer@example.com", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["token_type"] == "bearer"


def test_signup_rejects_password_mismatch(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "customer@example.com",
            "password": "strong-password",
            "confirm_password": "different-password",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
