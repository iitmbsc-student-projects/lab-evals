"""
Authentication endpoints for Google OAuth and JWT issuance.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import (
    get_or_create_user_from_google,
    issue_token_pair_for_user,
    rotate_token_pair,
    verify_google_id_token,
)

router = APIRouter()


class TokenRequest(BaseModel):
    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
def login(request: TokenRequest):
    claims = verify_google_id_token(request.id_token)
    try:
        user = get_or_create_user_from_google(claims)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )
    access_token, refresh_token, expires_in = issue_token_pair_for_user(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest):
    """Exchange a valid refresh token for a rotated token pair.

    Deliberately unauthenticated: the refresh token is itself the
    credential, and the access token it replaces is normally already
    expired, so no Authorization header is required.
    """
    try:
        access_token, refresh_token, expires_in = rotate_token_pair(
            request.refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
