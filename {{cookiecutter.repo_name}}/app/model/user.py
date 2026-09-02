"""사용자 도메인 모델: Role, UserRoleMapping, User, SmsVerification.

초기 세팅용 최소 필드 모델. 프로젝트 도메인 설계 확정 후 필드 확장 예정.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseIdCreatedAtModel, BaseIdModel, PublicIdMixin, SoftDeleteMixin


# ──────────────────────────────────────────────
# Role
# ──────────────────────────────────────────────
class Role(BaseIdModel):
    """역할 정의 (확장 가능한 RBAC)."""

    __tablename__ = "user_roles"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="역할 코드")
    display_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="표시명")
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="설명")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False, comment="활성 여부")


# ──────────────────────────────────────────────
# UserRoleMapping (M:N)
# ──────────────────────────────────────────────
class UserRoleMapping(BaseIdCreatedAtModel):
    """사용자-역할 M:N 매핑."""

    __tablename__ = "user_users_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_code", name="uq_user_users_roles"),)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_users.id"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )
    role_code: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("user_roles.code"),
        nullable=False,
        index=True,
        comment="역할 코드",
    )


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────
class User(BaseIdModel, PublicIdMixin, SoftDeleteMixin):
    """사용자 인증 기본 모델."""

    __tablename__ = "user_users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="이메일")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="비밀번호 해시")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="전화번호")
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="표시 이름")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'PENDING'"), comment="상태")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="삭제 일시")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="마지막 로그인 일시")

    # Relationships
    role_mappings: Mapped[list["UserRoleMapping"]] = relationship(lazy="raise")

    @property
    def roles(self) -> list[str]:
        """사용자의 역할 코드 목록을 반환한다. role_mappings가 로딩되어 있어야 한다."""
        return [rm.role_code for rm in self.role_mappings]


# ──────────────────────────────────────────────
# SmsVerification
# ──────────────────────────────────────────────
class SmsVerification(BaseIdCreatedAtModel):
    """SMS 인증코드 관리."""

    __tablename__ = "comn_sms_verifications"

    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="전화번호")
    code: Mapped[str] = mapped_column(String(6), nullable=False, comment="인증코드")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), comment="인증 여부")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), comment="시도 횟수")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="만료 일시")
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="인증 완료 일시")
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), comment="가입 사용 여부")
