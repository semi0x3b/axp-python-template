"""Backoffice 인증/인가 의존성 함수."""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum.response_message import ErrorResponseMessage
from app.core.exception.handlers import UnauthorizedError
from app.core.security.jwt_handler import decode_token
from app.db.connection import get_session
from app.model.admin import Admin

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> Admin:
    """JWT 토큰에서 현재 관리자를 조회한다.

    Authorization: Bearer <token> 헤더에서 토큰을 추출하고,
    admn_admins 테이블에서 관리자를 조회하여 상태를 검증한다.

    Raises:
        UnauthorizedError: 토큰 없음, 유효하지 않은 토큰, 삭제된 관리자.
    """
    if credentials is None:
        raise UnauthorizedError(detail=ErrorResponseMessage.UNAUTHORIZED)

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "admin_access":
        raise UnauthorizedError(detail=ErrorResponseMessage.INVALID_TOKEN)

    public_id = payload.get("sub")
    if not public_id:
        raise UnauthorizedError(detail=ErrorResponseMessage.INVALID_TOKEN)

    result = await session.execute(select(Admin).where(Admin.public_id == public_id))
    admin = result.scalar_one_or_none()

    if admin is None or admin.deleted_at is not None:
        raise UnauthorizedError(detail=ErrorResponseMessage.UNAUTHORIZED)

    return admin
