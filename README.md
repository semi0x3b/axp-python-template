# axp-python-template

![Python](https://img.shields.io/badge/python-3.13-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-async-green) ![cookiecutter](https://img.shields.io/badge/cookiecutter-template-orange)

FastAPI + SQLAlchemy 2.0 Async + PostgreSQL + Redis + Alembic 프로젝트를 찍어내는 cookiecutter 템플릿입니다. 새 API 프로젝트를 시작할 때마다 반복되는 초기 세팅(인증, 감사 로그, 마이그레이션, 테스트 기반, CI, 코딩 컨벤션 문서)을 한 번에 깔아 줍니다.

## Quick start

```bash
pipx install cookiecutter
cookiecutter gh:semi0x3b/axp-python-template
```

핵심 입력은 두 개뿐입니다. 나머지는 자동 파생되니 엔터로 넘기면 됩니다.

```
프로젝트 표시명 ('API' 제외, 예: Shop) [My]: Shop
GitHub 저장소명 / poetry 패키지명 / 폴더명 (kebab-case) [shop-api]:
```

생성 직후:

```bash
cd shop-api
cp .env.example .env       # ENCRYPTION_KEY 생성해 넣기
poetry install
make up                    # Docker: PostgreSQL + Redis
make revision MSG="init"   # 초기 migration
make migrate
make dev
```

## 무엇이 들어 있나

**애플리케이션**

| 영역 | 내용 |
|------|------|
| 앱 구조 | 앱 팩토리 + `APP_SERVICE` env로 멀티 서비스(`main`/`backoffice`/`job`) 분기 |
| DB | SQLAlchemy 2.0 async + asyncpg, `BaseRepository[T]` 제네릭 CRUD, Alembic async migrations |
| 모델 베이스 | `BaseIdModel`, `PublicIdMixin`(UUID), `SoftDeleteMixin`, 감사 필드 |
| 인증 | JWT access/refresh + Admin 토큰, M:N Role 접근 제어 |
| 미들웨어 | 구조화 로깅 + `X-Request-ID`, CORS, Swagger Basic Auth, 백오피스 감사 로그(자동 마스킹) |
| 설정 | pydantic-settings + AWS Secrets Manager source (환경별 자동 로드) |
| 기타 | Redis 이중 클라이언트(main + Pub/Sub), WebSocket connection manager, Job runner(`JOB_REGISTRY`), `/healthz`·`/readyz` |

**개발 기반**

| 영역 | 내용 |
|------|------|
| AI 컨벤션 | `.claude/` — 금지·필수 패턴(CLAUDE.md), 경로별 자동 로드 rules, 프로젝트 문서 세트, 커스텀 커맨드(컨벤션 검사·마이그레이션·커밋·테스트 생성·PR 본문 등), 도메인 구현 에이전트 템플릿 |
| 테스트 | `conftest.py`(env 자동 주입·`test_engine`·`clean_db`·서비스별 ASGI client) + 계약 테스트 |
| 훅 | pre-commit: 커밋 시 black + 변경분 단위 테스트, push 시 전체 단위 테스트 |
| 버전 | 서비스별 bumpversion + Makefile 타겟 + 버전 줄 자동 해결 머지 드라이버 |
| CI | main 빌드→이미지 push→gitops 태그 갱신→Slack 알림, main→하위 브랜치 자동 sync(충돌 시 PR) |
| 보안 | dev/prod에서 `JWT_SECRET_KEY`·`ENCRYPTION_KEY`가 코드 기본값이면 부팅 거부 |

## 변수

핵심 입력 (프로젝트마다 다름):

| 변수 | 용도 |
|------|------|
| `project_name` | Swagger 타이틀 표시명 (예: `Shop`) |
| `repo_name` | 저장소명 = 폴더명 = poetry 패키지명 (예: `shop-api`) |

파생값 (엔터로 스킵, 필요 시 오버라이드): `project_description`, `db_name`, `container_prefix`, `aws_secret_prefix`(`sm-<prefix>`), `author_name`, `author_email`, `python_version`, `output_parent`

## 생성 후 손봐야 할 것

| 파일 | 내용 |
|------|------|
| `.github/workflows/build-on-main.yml` | 레지스트리·gitops overlay 경로, 시크릿 4종 |
| `.github/workflows/sync-main-to-branches.yml` | Slack 채널·`SLACK_BOT_TOKEN` secret |
| `.github/CODEOWNERS` | 팀 핸들 |
| `.claude/projects/OVERVIEW.md` | 테이블·API 스냅샷 |
| `.claude/commands/migrate.md` | 운영 DB 호스트 패턴 (안전 체크용) |
| `.env` | `ENCRYPTION_KEY` — `python -c "import secrets; print(secrets.token_hex(32))"` |

## 템플릿에 없는 것

프로젝트별 배포 스크립트(`build.sh`, `Dockerfile.job`), IaC(`serverless/`, `deploy/`), 초기 migration 파일. 생성 후 각 프로젝트에서 추가합니다.

## 구조 규칙

- 도메인 디렉터리: `app/domain/<name>/{api,repo,schema,usecase}/`
- 새 모델은 `app/model/__init__.py`에 export (Alembic autogen 인식)
- 라우터 include는 `app/main.py`의 `APP_SERVICE` 분기 TODO 위치
