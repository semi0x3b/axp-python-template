# CLAUDE.md — 작업 규칙

{{cookiecutter.project_description}}. `APP_SERVICE` 환경변수로 main / backoffice / job 이미지를 분기 배포한다.

| 문서 | 내용 |
|------|------|
| `.claude/projects/OVERVIEW.md` | 테이블·API·env·에러코드 스냅샷 |
| `.claude/projects/CONVENTIONS.md` | 폴더구조·레이어 요약 |
| `.claude/projects/COMMANDS.md` | make·pytest·포트 |
| `.claude/projects/GLOSSARY.md` | 도메인 용어 |

코드 변경이 스펙과 어긋나면 `OVERVIEW.md` 동시 갱신.

---

## 절대 금지

- UseCase 없이 Router에서 비즈니스 로직
- Repository 우회 `session.execute()` 직접 호출
- 외부 API/URL에 내부 BigInt `id` 노출 (`public_id` 사용)
- `uuid.uuid4()` 직접 호출로 `public_id` 생성 (`PublicIdMixin` 기본값 / `app/core/utils/uuid_util.py` 사용)
- `session` 직접 사용 (IntegrityError flush 제외)

---

## 기술 스택

Python {{cookiecutter.python_version}} / FastAPI / SQLAlchemy 2.0 async / Pydantic v2 / Alembic / PostgreSQL / Redis
pytest + pytest-asyncio / Black (line-length 200) / mypy
진입점 `app/asgi.py` → `app/main.py:create_app()` | 설정 `app/core/config.py`

**테이블 prefix (4글자)**: `user_` `admn_` `comn_` `job_` — 신규 도메인 추가 시 4글자 prefix를 먼저 정하고 `OVERVIEW.md`에 기록

---

## 코딩 필수

**네이밍**: 모듈·함수·변수 `snake_case` / 클래스 `PascalCase` / 상수·Enum값 `UPPER_SNAKE_CASE` / private `_underscore`

**필수 패턴**:
- 모든 함수 I/O에 Type Hints
- 모든 DB 연산 `async/await`
- 로깅: `from app.core.logger import get_logger`
- 시간: `from app.core.utils.timezone import get_now` (직접 `datetime.now()` 금지)
- 공통 유틸: `app/core/utils/` 순수 함수만, DB 의존 금지

---

## 레이어별 세부 규칙

`.claude/rules/` — 해당 경로 파일 Read 시 자동 로드:
- `rules/api.md` — 인증 의존성·path 변수·응답 래퍼
- `rules/usecase.md` — ctx 패턴·메서드명·변환 메서드 금지
- `rules/repo.md` — BaseRepository·list 단일화·서비스 분리
- `rules/schema.md` — BaseSchema·public_id·SearchListRequest
- `rules/model.md` — PublicIdMixin·lazy="raise"·migration

완료 후 `/check-convention` 검사 필수.

## 커맨드

| 작업 | 커맨드 |
|------|--------|
| 컨벤션 전수 검사 | `/check-convention` |
| 마이그레이션 생성+적용 | `/migrate` |
| Gitmoji 커밋 + develop 반영 | `/commit-message` |
| 커밋만 (push 없음) | `/commit` |
| 워크트리 커밋 → 분기원 브랜치 로컬 머지 | `/wt-commit` |
| 테스트 실행·분석 | `/run-test [경로]` |
| 테스트 코드 생성 | `/generate-test [파일]` |
| OVERVIEW.md 코드 기준 갱신 | `/update-overview [--dry-run]` |
| 오늘/어제 작업 요약 | `/work-summary` |
| 서브에이전트 디스패치 시 컨벤션 블록 | `/context-subagent` |
| PR 본문 작성 + `gh pr create` | `/write-pr-description` |

## 에이전트

`.claude/agents/` — `domain-lead`(라우팅·온보딩) + `<domain>-expert`(도메인별 구현). 새 도메인이 생기면 `domain-lead` 에게 "X 도메인 에이전트 만들어줘" 로 온보딩. 템플릿은 `user-expert.md`.
