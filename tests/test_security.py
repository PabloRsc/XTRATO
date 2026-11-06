from app.security import verify_password


def test_invalid_password_hash_returns_false_instead_of_raising():
    assert verify_password("any-password", "not-a-valid-argon2-hash") is False
