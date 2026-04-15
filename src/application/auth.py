import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from src.config import JWT_EXPIRATION_HOURS, JWT_SECRET


def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")



def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])



def hash_password(password):
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{base64.b64encode(salt).decode('utf-8')}${base64.b64encode(derived_key).decode('utf-8')}"



def verify_password(password, stored_password):
    if not stored_password or "$" not in stored_password:
        return hmac.compare_digest(password, stored_password or "")

    salt_encoded, hash_encoded = stored_password.split("$", 1)
    salt = base64.b64decode(salt_encoded.encode("utf-8"))
    expected = base64.b64decode(hash_encoded.encode("utf-8"))
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(candidate, expected)



def is_token_valid(token):
    try:
        decode_token(token)
        return True
    except InvalidTokenError:
        return False
