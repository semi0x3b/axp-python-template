import math
from datetime import datetime
from typing import Any, List, Optional, TypeVar, Generic
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict, field_serializer

T = TypeVar("T")


class BaseRequestSchema(BaseModel):
    """요청 스키마용 베이스. datetime 직렬화 없이 Python 원시 타입을 유지한다."""

    model_config = ConfigDict(from_attributes=True)


class BaseSchema(BaseModel):
    """응답 스키마용 베이스. datetime → KST ISO 문자열로 직렬화한다."""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="always")
    def serialize_datetime(self, v, _info):
        if isinstance(v, datetime):
            return v.astimezone(ZoneInfo("Asia/Seoul")).isoformat()
        return v


class Pagination(BaseModel):
    total_count: Optional[int] = Field(None, description="전체 항목 수")
    total_page: Optional[int] = Field(None, description="전체 페이지 수")
    limit: Optional[int] = Field(None, description="페이지 당 항목 수")
    count: Optional[int] = Field(None, description="현재 페이지 항목 수")
    page: Optional[int] = Field(None, description="현재 페이지 번호")

    @classmethod
    def from_params(
        cls,
        *,
        page: int,
        limit: int,
        total_count: int,
        count: Optional[int] = None,
    ) -> "Pagination":
        """페이지네이션 파라미터로 Pagination 인스턴스를 생성한다."""
        total_page = 1 if limit <= 0 else max(1, math.ceil(total_count / limit))
        if count is None:
            offset = max(0, (page - 1) * max(1, limit))
            remaining = max(0, total_count - offset)
            count = min(max(0, limit), remaining)
        return cls(
            total_count=total_count,
            total_page=total_page,
            limit=limit,
            count=count,
            page=page,
        )


class IdSchema(BaseSchema):
    id: Any = Field(..., description="ID")


class CountSchema(BaseSchema):
    count: int = Field(..., description="항목 수")


class ErrorDetail(BaseSchema):
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    data: Optional[Any] = Field(None, description="에러 관련 추가 데이터")

    model_config = ConfigDict(from_attributes=True)


class SuccessBaseResponse(BaseSchema):
    """기본 성공 응답"""

    success: bool = Field(True, description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")


class SuccessResponse(SuccessBaseResponse, Generic[T]):
    """단일 데이터 성공 응답"""

    data: T = Field(..., description="응답 데이터")


class SuccessIdResponse(SuccessBaseResponse):
    """ID 성공 응답"""

    data: IdSchema = Field(..., description="ID")


class SuccessCountResponse(SuccessBaseResponse):
    """항목 수 성공 응답"""

    data: CountSchema = Field(..., description="항목 수")


class SuccessPaginationResponse(SuccessBaseResponse, Generic[T]):
    """페이지네이션이 포함된 리스트 데이터 성공 응답"""

    data: List[T] = Field(..., description="응답 데이터 목록")
    pagination: Pagination = Field(default_factory=Pagination, description="페이지네이션 정보")


class ErrorResponse(SuccessBaseResponse):
    """에러 응답"""

    error: ErrorDetail = Field(..., description="에러 정보")
