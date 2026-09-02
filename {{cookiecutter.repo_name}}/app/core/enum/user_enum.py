from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """기본 역할. 프로젝트 도메인 설계 시 확장 예정."""

    MEMBER = "MEMBER"
    PENDING = "PENDING"


class UserStatus(str, Enum):
    """사용자 상태."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    WITHDRAWN = "WITHDRAWN"
