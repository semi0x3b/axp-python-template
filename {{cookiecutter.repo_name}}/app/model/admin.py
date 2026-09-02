"""관리자 도메인 모델: Admin, AuditLog."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AbstractBaseModel, BaseIdModel, PublicIdMixin


# ──────────────────────────────────────────────
# Admin
# ──────────────────────────────────────────────
class Admin(BaseIdModel, PublicIdMixin):
    """멋컴(SUPER_ADMIN) 전용 테이블.

    일반 사용자(users)와 완전 분리된 별도 엔티티.
    대학 소속 없음, SMS 인증 불필요, 별도 가입 플로우.
    """

    __tablename__ = "admn_admins"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="이메일")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="비밀번호 해시")
    display_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="표시 이름 (실명)")
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'SUPER_ADMIN'"),
        comment="항상 SUPER_ADMIN",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="삭제 일시")


# ──────────────────────────────────────────────
# AuditLog
# ──────────────────────────────────────────────
class AuditLog(AbstractBaseModel):
    """관리자 행위 감사 로그 (append-only). 미들웨어가 자동 기록."""

    __tablename__ = "admn_audit_logs"
    __table_args__ = (
        Index("ix_admn_audit_logs_action", "action"),
        Index("ix_admn_audit_logs_actor_id", "actor_id"),
        Index("ix_admn_audit_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1), primary_key=True, index=True, comment="일련번호")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False, comment="생성일")

    actor_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("admn_admins.id"),
        nullable=True,
        comment="수행자 ID (비인증 요청은 NULL)",
    )
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="수행자 이메일 (비정규화)")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="행위 유형 (컨벤션 자동 생성)")
    http_method: Mapped[str] = mapped_column(String(10), nullable=False, comment="HTTP 메서드")
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False, comment="요청 URL path")
    route_group: Mapped[str] = mapped_column(String(50), nullable=False, comment="API 라우터 그룹")
    request_body: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True, comment="요청 body (민감 필드 마스킹)")
    response_body: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True, comment="응답 body")
    response_status: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="HTTP status code")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, comment="IP 주소")
