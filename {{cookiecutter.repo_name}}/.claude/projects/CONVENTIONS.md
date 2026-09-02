# 코드 컨벤션

> 레이어별 세부 규칙: `.claude/rules/` · 전수 검사: `/check-convention`

## 폴더 구조

```
app/domain/{main|backoffice|job}/     ← 서비스(배포 이미지) 단위
  version.py                          ← 서비스별 bumpversion 대상
  {서비스}_router.py                   ← 서비스 라우터 집합
  {도메인}/
    api/        ← {기능명}_api.py       (APIRouter() 만, prefix/tags 없음)
    repo/       ← {기능명}_repo.py
    usecase/    ← {기능명}_usecase.py
    schema/
      request/  ← {기능명}_request_schema.py
      response/ ← {기능명}_response_schema.py
    __init__.py
    {기능명}_router.py                 ← prefix/tags 선언 (tags는 한글)

app/model/      ← 모든 모델 (레이어 폴더 없음)
  __init__.py   ← Alembic autogenerate 진입점
```

- 모든 하위 디렉터리 `__init__.py` 필수
- 서비스 간 크로스 import 금지 (공유는 `app/core/`, `app/model/` 만)

## 핵심 규칙 요약

| 레이어 | 금지 |
|--------|------|
| Router | 비즈니스 로직·직접 DB 접근 |
| UseCase | HTTP 의존성·`session` 직접 사용(`IntegrityError` 제외)·직접 SQL |
| Repository | 비즈니스 로직·단일 테이블 직접 `select` |

- **식별자**: API 노출 → `public_id`(UUID). 내부 FK → `id`(BigInt)
- **응답 래퍼**: `SuccessResponse[T]` / `SuccessPaginationResponse[T]` / `SuccessBaseResponse`
- **목록 API**: `SearchListRequest = Depends()` 필수
- **상태값**: Enum `.value` 사용, 문자열 하드코딩 금지
- **API prefix**: main `/api/v1/`, backoffice `/api/v1/backoffice/`
- **UseCase 내 단일 호출 변환 메서드 금지**: `_to_response` 류는 호출 지점에 인라인
