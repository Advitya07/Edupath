"""Prototype token helpers. Replace with expiring signed JWTs in production."""
import base64
import json


def create_token(user_id: str) -> str:
    payload = json.dumps({"sub": user_id}).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_token(token: str | None) -> str:
    if not token:
        return "demo-user"
    try:
        return json.loads(base64.urlsafe_b64decode(token + "==")).get("sub", "demo-user")
    except Exception:
        return "demo-user"
