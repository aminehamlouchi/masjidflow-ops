from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


def hash_password(password: str) -> str:
    return hashlib.sha256(f"masjidflow:{password}".encode("utf-8")).hexdigest()


def _secret() -> bytes:
    return os.getenv("MASJIDFLOW_SECRET", "dev-secret-change-me").encode("utf-8")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_token(user_id: int, role: str, ttl_seconds: int = 8 * 60 * 60) -> str:
    payload = {"sub": user_id, "role": role, "exp": int(time.time()) + ttl_seconds}
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_secret(), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_b64encode(signature)}"


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(_secret(), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    provided = _b64decode(encoded_signature)
    if not hmac.compare_digest(expected, provided):
        return None

    payload = json.loads(_b64decode(encoded_payload))
    if payload.get("exp", 0) < time.time():
        return None
    return payload
