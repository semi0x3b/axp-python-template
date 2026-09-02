---
paths:
  - "app/domain/**/schema/**/*.py"
  - "app/core/schema/*.py"
---

## Schema 규칙

### 필수

**상속**: `BaseSchema` 상속 필수, `pydantic.BaseModel` 직접 상속 금지
```python
from app.core.schema.response import BaseSchema

class NoticeResponse(BaseSchema): ...   # ✅
class NoticeResponse(BaseModel): ...    # ❌
```

**식별자**: 응답에 `public_id: UUID` 사용, `id: int` 노출 금지

**목록 요청**: `SearchListRequest = Depends()` 사용, `page: int = Query(1)` 직접 선언 금지

**상태값**: `SomeEnum.VALUE.value` 사용, 문자열 리터럴 하드코딩 금지

**파일명**: `schema/request/{기능명}_request_schema.py`, `schema/response/{기능명}_response_schema.py`

**backoffice 스키마**: main 스키마 재사용 금지 → `Admin` 접두사 독립 스키마

### 권장

응답 필드 순서: `public_id` 먼저, 핵심 비즈니스 필드, 날짜(`created_at`, `updated_at`) 마지막
