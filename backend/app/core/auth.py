"""
Google OAuth ID token verification and user provisioning.
Handles JWT issuance after Google token verification.
"""

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import create_access_token
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


def issue_jwt_for_user(user: User) -> str:
    """Issue JWT for authenticated user."""
    return create_access_token({"user_id": user.id})
