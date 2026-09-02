import uuid
from typing import Any, Dict, Optional, Set
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, DateTime, String, Boolean, Identity, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AbstractBaseModel(Base):
    """모든 매핑 클래스가 공유하는 추상 베이스.

    공통 유틸(to_dict, __repr__)만 제공하며 컬럼은 정의하지 않는다.
    """

    __abstract__ = True

    def to_dict(self, exclude: Optional[Set[str]] = None) -> Dict[str, Any]:
        """모델 인스턴스를 딕셔너리로 변환한다."""
        exclude = exclude or set()
        result: Dict[str, Any] = {}
        for col in self.__table__.columns:
            if col.name in exclude:
                continue
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                seoul_tz = ZoneInfo("Asia/Seoul")
                value = value.astimezone(seoul_tz).isoformat()
            result[col.name] = value
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"


class BaseModel(AbstractBaseModel):
    """감사 공통 필드(created_at/updated_at/created_by/updated_by)를 제공하는 베이스 모델."""

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="생성일",
    )
    created_by: Mapped[str] = mapped_column(
        String(50),
        server_default=text("'system'"),
        nullable=False,
        comment="생성자",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="수정일",
    )
    updated_by: Mapped[str] = mapped_column(
        String(50),
        server_default=text("'system'"),
        nullable=False,
        comment="수정자",
    )


class BaseIdModel(BaseModel):
    """id(BigInt) + 감사 필드를 제공하는 베이스 모델."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(start=1, increment=1),
        primary_key=True,
        index=True,
        comment="일련번호",
    )


class BaseIdCreatedAtModel(BaseModel):
    """id(BigInt) + 감사 필드를 제공하는 베이스 모델.

    로그, 매핑 테이블 등에 사용한다.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(start=1, increment=1),
        primary_key=True,
        index=True,
        comment="일련번호",
    )


class SoftDeleteMixin:
    """Soft Delete 기능을 제공하는 Mixin.

    게시글, 댓글 등에 사용한다.
    """

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        comment="활성 상태",
    )


class PublicIdMixin:
    """외부 노출용 UUID를 제공하는 Mixin.

    API 응답, URL 경로 등 외부에 ID를 노출해야 하는 엔티티에 사용한다.
    내부 BigInt PK는 DB 조인/인덱스 성능용, public_id는 외부 식별용.
    """

    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
        index=True,
        comment="외부 노출용 UUID",
    )
