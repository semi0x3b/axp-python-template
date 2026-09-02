---
paths:
  - "app/domain/**/repo/*.py"
---

## Repository 규칙

### 필수

**BaseRepository 메서드만 사용**:
- 단건: `get_by(field=value)`, `get_by_public_id(uuid)`
- 목록: `get_list_with_pagination(filters=dict, sort=, page=, limit=)`
- 생성/수정: `create(obj_in: dict)`, `update(obj, obj_in)`, `soft_delete(obj)`

**list 메서드 단일화**: 조건별 메서드 분리 금지 → `filters: dict` 받는 단일 메서드
```python
# ❌
async def list_by_user(self, user_id): ...
async def list_by_job(self, job_id): ...

# ✅
async def list_notices(self, filters: dict, page: int, limit: int):
    return await self.get_list_with_pagination(filters=filters, page=page, limit=limit)
```

**서비스 분리**: `app/domain/backoffice/`는 `app/domain/main/` 하위 repo import 금지 → `backoffice/{도메인}/repo/`에 별도 생성

### 금지

- 비즈니스 로직 (조건 분기, 상태 변환)
- 단순 단건 조회에 `session.execute(select(...))` 직접 작성

### 권장

JOIN / OR / 범위 조건 등 복잡한 쿼리는 별도 메서드 OK.
id projection 선조회 헬퍼(`find_ids_by_name` 등)는 `select(Model.id)` + `session.execute` 직접 작성 OK — "단순 단건 조회 금지" 규칙의 예외.
빈 id 목록이 넘어오면 0건 가드(`Model.id == -1`)로 전체 조회를 막는다.
