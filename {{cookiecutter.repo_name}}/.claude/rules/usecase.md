---
paths:
  - "app/domain/**/usecase/*.py"
---

## UseCase 규칙

### 필수

**시그니처**: 항상 `__init__(session, user=None)` + `_require_user()` 패턴
```python
class NoticeUsecase:
    def __init__(self, session: AsyncSession, user: User | None = None):
        self.session = session
        self.user = user  # Router 가 get_current_user 로 주입

    def _require_user(self) -> User:
        if self.user is None:
            raise RuntimeError("user required")
        return self.user
```
- 메서드 파라미터로 `user_id` / `user_email` 직접 받지 않음

**메서드명**: 동사 + 대상 모델명 필수
- ❌ `create()`, `get()`, `list()`, `list_mine()`
- ✅ `create_notice()`, `get_my_notice_detail()`, `list_notices_by_user()`

**목록 검색**: `params.search_filter`(`SearchListRequest`의 filters DSL)에서 추출
- 대상 모델 직접 컬럼: 추출값을 `filters` dict로 Repo에 전달 → Repo가 blind index / ILIKE 처리
- JOIN 필요 검색: UseCase에서 해당 테이블 **선조회** → id 목록 → `xxx_id IN`으로 변환해 Repo 전달. JOIN을 Repo에 떠넘기지 않음

### 금지

- `session.execute()` 직접 호출 (IntegrityError flush 목적 제외)
- HTTP 의존성 import (`Request`, `Response`, `Header` 등)
- `_to_response()` / `_to_list_item()` 단일 호출 static 변환 메서드 — 호출 지점에 인라인 작성
