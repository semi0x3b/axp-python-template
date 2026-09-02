---
paths:
  - "app/domain/**/api/*.py"
  - "app/domain/**/*_router.py"
---

## API / Router 규칙

### 필수

**인증 의존성**: 서비스 간 혼용 금지
```python
# main 서비스
from app.core.security.auth_dependency import get_current_user, require_role

# backoffice 전용
from app.core.security.admin_auth_dependency import get_current_admin
```

**path 변수**: 약식 금지, 리소스명 포함 풀네임
- ❌ `{uid}`, `{pid}`, `{public_id}`
- ✅ `{user_public_id}`, `{job_public_id}`

**응답**: `SuccessResponse[T]` / `SuccessPaginationResponse[T]` 래퍼 필수

**prefix/tags 위치**: `_api.py`에는 `APIRouter()` 만, `prefix`·`tags`는 `_router.py`에서 선언하고 `tags`는 한글
```python
# _api.py
router = APIRouter()

# _router.py
router = APIRouter(prefix="/api/v1/notices", tags=["공지사항"])
router.include_router(notice_api_router)
```

### 금지

- 비즈니스 로직, DB 직접 접근 — 반드시 UseCase 경유
- 목록 검색 전용 쿼리 파라미터(`keyword`·`search_field` 등) 신설 — `SearchListRequest`의 `filters` DSL 사용

### 권장

라우트 순서: 정적 경로 → 동적 경로 (`/me` 먼저, `/{public_id}` 나중)
