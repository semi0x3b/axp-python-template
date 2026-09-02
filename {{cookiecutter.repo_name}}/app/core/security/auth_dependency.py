"""FastAPI 인증/인가 의존성 함수."""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enum.response_message import ErrorResponseMessage
from app.core.enum.user_enum import UserRole, UserStatus
from app.core.exception.handlers import ForbiddenError, UnauthorizedError
from app.core.logger import get_logger
from app.core.security.jwt_handler import decode_token
from app.db.connection import get_session
from app.model.user import User

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """JWT 토큰에서 현재 사용자를 조회한다.

    Authorization: Bearer <token> 헤더에서 토큰을 추출하고,
    DB에서 사용자를 조회하여 상태를 검증한다.
    role_mappings를 selectinload로 함께 로딩한다.

    Raises:
        UnauthorizedError: 토큰 없음, 유효하지 않은 토큰, 비활성 사용자.
    """
    if credentials is None:
        raise UnauthorizedError(detail=ErrorResponseMessage.UNAUTHORIZED)

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise UnauthorizedError(detail=ErrorResponseMessage.INVALID_TOKEN)

    public_id = payload.get("sub")
    if not public_id:
        raise UnauthorizedError(detail=ErrorResponseMessage.INVALID_TOKEN)

    result = await session.execute(select(User).options(selectinload(User.role_mappings)).where(User.public_id == public_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise UnauthorizedError(detail=ErrorResponseMessage.UNAUTHORIZED)

    if user.status == UserStatus.BANNED.value:
        raise UnauthorizedError(detail=ErrorResponseMessage.ACCOUNT_BANNED)

    if user.status == UserStatus.WITHDRAWN.value:
        raise UnauthorizedError(detail={"code": "ERR-2006", "message": "탈퇴한 계정입니다."})

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """토큰이 없으면 None을 반환한다 (비회원 허용 API용)."""
    if credentials is None:
        return None
    return await get_current_user(credentials=credentials, session=session)


def require_role(*allowed_roles: UserRole):
    """역할 기반 접근 제어 의존성 팩토리 (M:N 지원).

    사용자의 역할 목록 중 하나라도 allowed_roles에 포함되면 통과.

    Args:
        *allowed_roles: 접근을 허용할 UserRole 목록.

    Returns:
        FastAPI Depends에 사용할 의존성 함수.
    """

    async def _check_role(
        current_user: User = Depends(get_current_user),
    ) -> None:
        allowed_values = {r.value for r in allowed_roles}
        if not set(current_user.roles) & allowed_values:
            raise ForbiddenError(detail=ErrorResponseMessage.FORBIDDEN)

    return _check_role
