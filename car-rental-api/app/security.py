from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .database import get_db

PASSWORD_ITERATIONS = 210_000
SESSION_DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def create_session(db: Session, user: models.User) -> str:
    raw_token = secrets.token_urlsafe(32)
    session = models.AuthSession(
        token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=SESSION_DAYS),
    )
    db.add(session)
    db.commit()
    return raw_token


admin_bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="AdminBearer",
    description=(
        "Administrator token returned by POST /admin/login. "
        "Required for /users, /vehicles, /locations, /bookings and /invoices management endpoints."
    ),
)


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="CustomerBearer",
    description=(
        "Customer access token returned by POST /auth/login or "
        "POST /auth/register. In Swagger click Authorize and paste "
        "the token only; Swagger adds the Bearer prefix automatically."
    ),
)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    return credentials.credentials


def get_current_user(
    raw_token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> models.User:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(UTC)

    auth_session = db.scalar(
        select(models.AuthSession).where(
            models.AuthSession.token_hash == token_hash,
            models.AuthSession.expires_at > now,
        )
    )
    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    user = db.get(models.User, auth_session.user_id)
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable",
        )
    return user


def delete_current_session(
    raw_token: str,
    db: Session,
) -> None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    auth_session = db.scalar(
        select(models.AuthSession).where(models.AuthSession.token_hash == token_hash)
    )
    if auth_session is not None:
        db.delete(auth_session)
        db.commit()


def _resolve_user_from_token(raw_token: str, db: Session) -> models.User:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(UTC)
    auth_session = db.scalar(
        select(models.AuthSession).where(
            models.AuthSession.token_hash == token_hash,
            models.AuthSession.expires_at > now,
        )
    )
    if auth_session is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    user = db.get(models.User, auth_session.user_id)
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="User account is unavailable")
    return user


def get_admin_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Security(admin_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Administrator authentication required")
    return credentials.credentials


def get_current_admin(
    raw_token: str = Depends(get_admin_bearer_token),
    db: Session = Depends(get_db),
) -> models.User:
    user = _resolve_user_from_token(raw_token, db)
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
