import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    pw = "SuperSecureP@ss123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    user_id = "user-uuid-12345"
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id


def test_auth_api_flow(client):
    # Register
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@corp.com",
            "password": "Password123!",
            "full_name": "New Corporate User",
        }
    )
    assert reg_res.status_code == 200
    token_data = reg_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Access /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "newuser@corp.com"

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "newuser@corp.com", "password": "Password123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
