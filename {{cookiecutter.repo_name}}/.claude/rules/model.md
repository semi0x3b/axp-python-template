---
paths:
  - "app/model/*.py"
---

## Model 규칙

### 필수

**테이블명**: 4글자 도메인 prefix + 복수형 (`user_users`, `admn_audit_logs`, `comn_file_uploads`)

**API 노출 모델은 `PublicIdMixin` 필수** — 응답 스키마에서 참조되는데 `public_id`가 없으면 위반.
예외: 순수 연결 테이블, 조회 API가 없는 로그성 모델.

**관계 필드 `lazy="raise"` 필수** — 누락 시 async 환경에서 lazy load → `MissingGreenlet` 500.
```python
author: Mapped["User"] = relationship("User", lazy="raise")
```

**신규 모델은 `app/model/__init__.py`에 export** — Alembic autogenerate 진입점.

### 마이그레이션

모델 변경 후 `make revision MSG="..."` → 생성된 파일 검토 → `make migrate`.
마이그레이션 파일을 손으로 먼저 만들지 않는다.
