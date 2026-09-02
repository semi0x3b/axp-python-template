"""JWT 토큰 생성 및 검증."""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.enum.response_message import ErrorResponseMessage
from app.core.exception.handlers import UnauthorizedError


def create_access_token(public_id: str) -> str:
    """Access Token 생성.

    Args:
        public_id: 사용자 public_id (UUID 문자열).

    Returns:
        JWT 인코딩된 access token 문자열.
    """
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": public_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(public_id: str) -> str:
    """Refresh Token 생성.

    Args:
        public_id: 사용자 public_id (UUID 문자열).

    Returns:
        JWT 인코딩된 refresh token 문자열.
    """
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": public_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT 토큰 디코딩 및 검증.

    Args:
        token: JWT 토큰 문자열.

    Returns:
        디코딩된 payload dict.

    Raises:
        UnauthorizedError: 토큰이 만료되었거나 유효하지 않은 경우.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(detail=ErrorResponseMessage.TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise UnauthorizedError(detail=ErrorResponseMessage.INVALID_TOKEN)


# ──────────────────────────────────────────────
# Admin 전용 토큰
# ──────────────────────────────────────────────
def create_admin_access_token(public_id: str, role: str = "SUPER_ADMIN") -> str:
    """Admin Access Token 생성.

    Args:
        public_id: 관리자 public_id (UUID 문자열).
        role: 관리자 역할.

    Returns:
        JWT 인코딩된 admin access token 문자열.
    """
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": public_id,
        "role": role,
        "type": "admin_access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_admin_refresh_token(public_id: str) -> str:
    """Admin Refresh Token 생성.

    Args:
        public_id: 관리자 public_id (UUID 문자열).

    Returns:
        JWT 인코딩된 admin refresh token 문자열.
    """
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": public_id,
        "type": "admin_refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
