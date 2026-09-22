"""
Google OAuth ID token verification and user provisioning.
Handles JWT issuance after Google token verification.
"""

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.user import User

settings = get_settings()


def verify_google_id_token(id_token_str: str) -> dict:
    """Verify Google ID token and return claims."""
    try:
        claims = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return claims
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        )


def get_or_create_user_from_google(claims: dict) -> User:
    """Get or bind a pre-enrolled user from Google OAuth claims."""
    sub = claims["sub"]
    email = claims["email"]
    name = claims.get("name", "Unknown")

    db = SessionLocal()
    try:
        # 1. Prefer stable identity lookup
        user = db.query(User).filter_by(google_sub=sub).one_or_none()
        if user:
            return user

        # 2. Fallback to pre-enrolled email
        user = db.query(User).filter_by(email=email).one_or_none()
        if not user:
            raise ValueError("User not enrolled")

        # 3. Bind google_sub on first login
        if user.google_sub is None:
            user.google_sub = sub
            if not user.name:
                user.name = name
            db.commit()
            db.refresh(user)
            return user

        # 4. Email exists but bound to a different Google account
        raise ValueError("Google account does not match enrolled user")

    finally:
        db.close()


def issue_token_pair_for_user(user: User) -> tuple[str, str, int]:
    """Issue (access_token, refresh_token, expires_in_seconds) for a user."""
    claims = {"user_id": user.id}
    return (
        create_access_token(claims),
        create_refresh_token(claims),
        settings.JWT_EXPIRES_MINUTES * 60,
    )


def rotate_token_pair(refresh_token: str) -> tuple[str, str, int]:
    """Validate a refresh token and issue a rotated token pair.

    Raises ValueError if the token is not a valid, unexpired refresh
    token, or if the user it names no longer exists.
    """
    try:
        payload = decode_refresh_token(refresh_token)
    except ValueError as e:
        raise ValueError("Invalid or expired refresh token") from e

    user_id = payload.get("user_id")
    if user_id is None:
        raise ValueError("Invalid or expired refresh token")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).one_or_none()
        if not user:
            # Same message as a bad token: do not reveal whether the
            # account behind a validly signed token still exists.
            raise ValueError("Invalid or expired refresh token")
        return issue_token_pair_for_user(user)
    finally:
        db.close()
