from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_round_trip() -> None:
    password = "correct-horse-battery-staple"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_access_token_round_trip() -> None:
    token = create_access_token("user-id", {"role": "admin"})
    claims = decode_access_token(token)

    assert claims["sub"] == "user-id"
    assert claims["role"] == "admin"
    assert claims["type"] == "access"
