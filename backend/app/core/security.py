"""Token handling for the backend API.

This module deliberately does **not** define a second authentication system.
Access tokens are issued by the Authentication module (the root ``app/``
FastAPI application). This file only *verifies* those tokens, using the same
contract:

    algorithm : HS256
    secret    : settings.SECRET_KEY
    claims    : {"sub": <user id>, "exp": <expiry>, "role": <role, optional>}

Keeping verification here means every module in ``backend/app`` can depend on
the identity of the caller without importing the Authentication module or
querying its database.
"""

from __future__ import annotations

from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify an access token, returning its claims.

    Returns ``None`` when the token is malformed, tampered with, or expired,
    so callers can translate that into a 401 without leaking the reason.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
