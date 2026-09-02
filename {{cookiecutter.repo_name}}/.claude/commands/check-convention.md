---
description: 레이어 컨벤션 전수 검사 및 수정
allowed-tools: Bash(grep:*), Bash(rg:*), Bash(ls:*), Read, Edit
---

# 컨벤션 전수 검사

`.claude/rules/` 의 규칙을 기준으로 변경 파일(또는 `$ARGUMENTS` 지정 경로)을 검사하고 위반을 수정한다.
규칙 원문은 rules 파일이 진실원 — 이 커맨드는 검사 절차만 정의한다.

## 검사 순서 (빈번한 위반 우선)

| 우선순위 | 규칙 | 근거 |
|----------|------|------|
| ★★★ | 응답 스키마에 `id` 노출 | `rules/schema.md` |
| ★★★ | `session.execute()` 직접 호출 | `rules/repo.md`, `rules/usecase.md` |
| ★★★ | 서비스 간 크로스 import (main ↔ backoffice) | `projects/CONVENTIONS.md` |
| ★★★ | `pydantic.BaseModel` 직접 상속 | `rules/schema.md` |
| ★★★ | `relationship(...)` 에 `lazy="raise"` 누락 | `rules/model.md` |
| ★★ | UseCase 메서드명 모호 (`create()` 등) | `rules/usecase.md` |
| ★★ | `list_by_xxx` 식 분리 메서드 | `rules/repo.md` |
| ★★ | 목록 API `SearchListRequest` 미사용 | `rules/schema.md` |
| ★★ | `_api.py` 에 `prefix`/`tags` 선언, 영문 `tags` | `rules/api.md` |
| ★ | 단일 호출 static 변환 메서드 (`_to_response()`) | `rules/usecase.md` |

## 기계 검사 (먼저 실행)

```bash
grep -rn "session.execute(" app/domain --include="*_usecase.py"
grep -rn "relationship(" app/model | grep -v 'lazy="raise"'
grep -rn "class .*(BaseModel)" app/domain --include="*_schema.py"
grep -rn "from app.domain.backoffice" app/domain/main app/domain/job 2>/dev/null
grep -rn "from app.domain.main" app/domain/backoffice app/domain/job 2>/dev/null
grep -rn "APIRouter(prefix=\|APIRouter(tags=" app/domain --include="*_api.py"
```

## 출력 형식

파일별로 `파일:줄번호 — 위반 규칙 — 수정 내용` 한 줄씩. 위반 0건이면 "통과"만 출력.
수정이 마이그레이션을 유발하면(모델 변경) 직접 생성하지 말고 `make revision MSG="..."` 실행을 안내한다.
