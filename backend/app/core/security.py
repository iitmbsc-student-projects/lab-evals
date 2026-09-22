"""
JWT encoding and decoding helpers for authentication.

Tokens carry a ``typ`` claim so an access token and a refresh token are
never interchangeable: only ``access`` tokens are accepted as bearer
credentials, and only ``refresh`` tokens can be exchanged at
``/api/v1/auth/refresh``.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _create_token(data: dict, token_type: str, expire: datetime) -> str:
    """Encode a JWT with an expiry and a token-type claim."""
    to_encode = data.copy()
    to_encode.update({"exp": expire, "typ": token_type})
    return jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    """Create a short-lived JWT access token (expires_delta: minutes)."""
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_delta or settings.JWT_EXPIRES_MINUTES
    )
    return _create_token(data, TOKEN_TYPE_ACCESS, expire)


def create_refresh_token(data: dict, expires_delta: int | None = None) -> str:
    """Create a long-lived JWT refresh token (expires_delta: days)."""
    expire = datetime.now(UTC) + timedelta(
        days=expires_delta or settings.REFRESH_TOKEN_EXPIRES_DAYS
    )
    return _create_token(data, TOKEN_TYPE_REFRESH, expire)


def decode_token(token: str, expected_type: str) -> dict:
    """Decode a JWT and assert its ``typ`` claim matches expected_type."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as e:
        raise ValueError("Invalid token") from e
    # TODO(2026-09-22): the TOKEN_TYPE_ACCESS default accepts tokens
    # minted before the typ claim existed as access tokens; drop it
    # (plain ``payload.get("typ")``) once that legacy window has closed.
    # Those tokens also carry a naive local-time exp, so on an IST
    # container they are honoured about 5.5h longer than nominal.
    if payload.get("typ", TOKEN_TYPE_ACCESS) != expected_type:
        raise ValueError(f"Expected a {expected_type} token")
    return payload


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token."""
    return decode_token(token, TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> dict:
    """Decode a JWT refresh token."""
    return decode_token(token, TOKEN_TYPE_REFRESH)
