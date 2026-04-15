from src.application.auth import hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    password = "StrongPass123"
    stored = hash_password(password)

    assert stored != password
    assert "$" in stored
    assert verify_password(password, stored)



def test_verify_password_supports_legacy_plaintext_for_migration():
    assert verify_password("password123", "password123")
    assert not verify_password("wrong", "password123")
