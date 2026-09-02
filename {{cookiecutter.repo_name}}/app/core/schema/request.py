"""Request Schemas

공통 요청 스키마를 정의합니다.
"""

from typing import Optional, Any, List

from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from app.core.schema.search_request import SearchFilter


class IdRequest(BaseModel):
    id: Any = Field(..., description="고유 ID")


class PaginationRequest(BaseModel):
    """페이지네이션 요청"""

    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)")
    limit: int = Query(20, ge=1, le=100, description="페이지 당 항목 수 (최대 100)")


class SortRequest(BaseModel):
    """정렬 요청"""

    sort: Optional[str] = Query(
        None,
        description="정렬 쿼리 스트링 (예: created_at,-user_id,name)",
    )

    @field_validator("sort", mode="before")
    def split_and_validate(cls, v):
        if not v:
            return None
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    @property
    def sort_list(self) -> Optional[List[str]]:
        """sort 문자열을 리스트로 변환한다."""
        if not self.sort:
            return None
        items = [s.strip() for s in self.sort.split(",") if s.strip()]
        for item in items:
            field_name = item.lstrip("-")
            if not field_name.replace("_", "").replace(".", "").isalnum():
                raise ValueError(f"잘못된 정렬 필드: {item}")
        return items


class ListRequest(PaginationRequest, SortRequest):
    """리스트 요청 (페이지네이션 + 정렬)"""

    pass


class SearchListRequest(ListRequest):
    """검색 기능이 있는 목록 조회 요청

    filters 쿼리 파라미터 예시:
    - 단일 조건: filters=status:active
    - LIKE 검색: filters=name:`test`
    - 다중 값: filters=category:backend,devops
    - 복합 조건: filters=name:`semi`|category:backend
    """

    filters: Optional[str] = Query(
        None,
        description=(
            "필터 쿼리 스트링.\n\n"
            "**문법**: `컬럼:값` 형식, 여러 조건은 `|`로 구분\n\n"
            "| 패턴 | 문법 | 예시 |\n"
            "|------|------|------|\n"
            "| 일치 (EQUAL) | `컬럼:값` | `status:ACTIVE` |\n"
            "| 부분 검색 (LIKE) | 컬럼:\\`값\\` | name:\\`홍\\` |\n"
            "| 다중 값 (IN) | `컬럼:값1,값2` | `role:MEMBER,PENDING` |\n"
            "| 다중 컬럼 OR | `컬럼1,컬럼2:값` | `email,nickname:semi` |\n"
            "| 다중 컬럼 OR LIKE | 컬럼1,컬럼2:\\`값\\` | email,nickname:\\`김\\` |\n"
            "| 복합 조건 | 조건1\\|조건2 | status:ACTIVE\\|role:MEMBER |\n\n"
            "**참고**: 백틱(\\`)은 LIKE 와일드카드(%)로 변환, 쉼표는 IN 또는 OR 구분자"
        ),
    )

    @property
    def search_filter(self) -> Optional[SearchFilter]:
        """filters 문자열을 SearchFilter 객체로 변환한다."""
        if self.filters:
            return SearchFilter.from_query_string(self.filters)
        return None
