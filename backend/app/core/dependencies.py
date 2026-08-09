"""Shared request dependencies: caller identity and role checks.

Identity comes from the access token issued by the Authentication module
(see ``app.core.security``). Nothing here creates users or sessions — this is
purely the consuming side of the existing authentication contract.

Two roles are in use across the product: ``admin`` and ``user``. Any role that
is not ``admin`` is treated as ``user``, so tokens minted before roles were
added to the claim set degrade to the least-privileged role rather than
accidentally granting administrative access.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_access_token

ROLE_ADMIN = "admin"
ROLE_USER = "user"

# auto_error=False so we can distinguish "no credentials supplied" (which the
# prototype fallback below may allow) from "bad credentials" (never allowed).
_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated caller, as far as this API is concerned."""

    id: int | None
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def actor(self) -> str:
        """Short label recorded on activity/audit trails."""
        return f"user:{self.id}" if self.id is not None else "anonymous"


def _normalize_role(raw: object) -> str:
    return ROLE_ADMIN if str(raw or "").strip().lower() == ROLE_ADMIN else ROLE_USER


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Resolve the caller from the ``Authorization: Bearer <token>`` header.

    When no credentials are supplied and ``AUTH_REQUIRED`` is disabled, the
    caller is treated as an anonymous non-admin user. That mirrors the existing
    mailer dry-run convention (``app.services.mailer_service``) so the module
    stays demonstrable before the login UI exists — it is *not* a way to skip a
    check: a token that is present but invalid is always rejected, and the
    anonymous identity never receives the admin role.
    """
    if credentials is None or not credentials.credentials:
        if settings.AUTH_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return CurrentUser(id=None, role=ROLE_USER)

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return CurrentUser(id=user_id, role=_normalize_role(payload.get("role")))


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Restrict an endpoint to administrators."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This action requires the admin role.",
        )
    return current_user
