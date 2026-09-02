# axp-python-template

FastAPI + SQLAlchemy 2.0 Async + PostgreSQL + Redis + Alembic 기반 Python API 프로젝트 cookiecutter 템플릿.

## 제공 기능

- **FastAPI 앱 팩토리** + `APP_SERVICE` env 기반 멀티 서비스(`main`/`backoffice`/`job`) 분기
- **SQLAlchemy 2.0 async** + asyncpg + `BaseRepository[T]` 제네릭 CRUD
- **모델 베이스**: `BaseIdModel`, `PublicIdMixin`(UUID), `SoftDeleteMixin`, 감사 필드
- **인증**: JWT access/refresh + Admin 토큰, M:N Role 기반 접근 제어
- **미들웨어**: 구조화 로깅 + `X-Request-ID`, CORS, Swagger Basic Auth, 백오피스 감사 로그(자동 마스킹)
- **Redis 이중 클라이언트** (main + chat Pub/Sub)
- **Alembic async migrations**
- **pydantic-settings** + AWS Secrets Manager source (환경별 자동 로드)
- **헬스체크** (`/healthz`, `/readyz`)
- **Job runner** (EventBridge 구동, `JOB_REGISTRY` 기반)
- **WebSocket** + Redis Pub/Sub connection manager
- Placeholder 모델: User / Admin / AuditLog / FileUpload / JobResult / NotificationTemplate / SmsVerification

### 컨벤션 자산

- **`.claude/`**: `CLAUDE.md`(절대 금지·필수 패턴) + `rules/{api,usecase,repo,schema,model}.md`(경로별 자동 로드) + `projects/{OVERVIEW,CONVENTIONS,COMMANDS,GLOSSARY}.md` + `commands/`(check-convention·migrate·commit-message·commit·wt-commit·run-test·generate-test·update-overview·work-summary·context-subagent) + `agents/`(domain-lead + user-expert 템플릿 — 도메인별 구현 에이전트 패턴) + `commands/write-pr-description`(PR 본문 작성·생성)
- **`.pre-commit-config.yaml`**: 커밋 시 black + 변경분 단위 테스트, push 시 단위 테스트 전체 (`migration` 브랜치 skip)
- **`tests/`**: `conftest.py`(env 자동 주입 / `test_engine` / `clean_db` / 서비스별 ASGI client) + 계약 테스트 2종
- **버전 관리**: 서비스별 `.bumpversion.*.cfg` + Makefile `bump-*` 타겟 + 버전 줄 자동 해결 머지 드라이버(`.gitattributes`)
- **`.github/`**: `build-on-main.yml`(version.py bump → 서비스별 이미지 빌드 → OCIR → gitops newTag → Slack) + `sync-main-to-branches.yml`(main → develop·migration 자동 머지, 충돌 시 sync PR + Slack) + 충돌 분류 스크립트 + CODEOWNERS
- **보안 안전장치**: 운영(dev/prod)에서 `JWT_SECRET_KEY`·`ENCRYPTION_KEY` 가 코드 기본값이면 부팅 거부 + 단위 테스트
- **`.dockerignore`**, **`http/`** (IntelliJ HTTP Client)

## 사용법

### 설치

```bash
pipx install cookiecutter  # 또는 pip install --user cookiecutter
```

### 프로젝트 생성

```bash
cookiecutter gh:semi0x3b/axp-python-template

프로젝트 표시명 ('API' 제외, 예: ATS) [My]: ATS
GitHub 저장소명 / poetry 패키지명 / 폴더명 (kebab-case) [ats-api]:
프로젝트 설명 [엔터로 기본값] [ATS 백엔드 API]:
PostgreSQL DB 이름 [엔터로 기본값] [ats]:
Docker 컨테이너 prefix [엔터로 기본값] [ats]:
AWS Secrets Manager prefix [엔터로 기본값] [sm-ats]:
작성자 이름 [엔터로 기본값] [semi]:
작성자 이메일 [엔터로 기본값] [you@example.com]:
Python 버전 [엔터로 기본값] [3.13]:
생성 위치 상위 경로 (. = 현재 디렉터리) [.]: ~/workspace/23.ats
```

**핵심 입력은 첫 2개 (`project_name`, `repo_name`)**. 나머지는 자동 파생 — 엔터로 스킵.

cookiecutter는 `output_parent` 경로에 `{repo_name}/` 생성 후 자동 `git init`.

### 생성 이후

```bash
cd ats-api
cp .env.example .env
poetry install
make up                    # Docker: PostgreSQL + Redis
make revision MSG="init"   # 초기 migration
make migrate
make dev
```

## 변수

| 변수 | 기본값 / 파생 | 용도 |
|------|-------------|------|
**핵심 입력** (프로젝트마다 다름):

| 변수 | 용도 |
|------|------|
| `project_name` | Swagger 타이틀 표시명 ("API" 제외, 예: "ATS") |
| `repo_name` | GitHub 저장소명 = 로컬 폴더명 = poetry 패키지명 (예: "ats-api") |

**파생값** (엔터로 스킵, 필요 시 오버라이드):

| 변수 | 기본 파생 |
|------|----------|
| `project_description` | `"{project_name} 백엔드 API"` |
| `db_name` | `project_name` 소문자 snake_case |
| `container_prefix` | `db_name` |
| `aws_secret_prefix` | `"sm-{container_prefix}"` |
| `author_name` | `"semi"` |
| `author_email` | `"you@example.com"` |
| `python_version` | `"3.13"` |
| `output_parent` | `"."` (현재 cwd). `~/workspace/23.ats` 지정 시 해당 경로로 이동 |

## 생성 후 손봐야 할 것

| 파일 | 내용 |
|------|------|
| `.github/workflows/build-on-main.yml` | `env` 블록의 레지스트리·gitops overlay 경로, 시크릿 4종 |
| `.github/workflows/sync-main-to-branches.yml` | Slack 채널·`SLACK_BOT_TOKEN` secret 확인 |
| `.github/CODEOWNERS` | 팀 핸들 확인 |
| `.claude/projects/OVERVIEW.md` | 테이블·API 스냅샷 채우기 |
| `.claude/commands/migrate.md` | 운영 DB 호스트 패턴 명시 (Step 1 안전 체크) |
| `.env` | `ENCRYPTION_KEY` 생성 (`python -c "import secrets; print(secrets.token_hex(32))"`) |

## 템플릿에서 제외됨

- 프로젝트별 배포 스크립트 (`build.sh`, `build_base.sh`, `Dockerfile.job`)
- `serverless/`, `deploy/` (프로젝트별 IaC)
- 초기 migration (`migrations/versions/*.py`)

생성 후 프로젝트에서 필요 시 추가.

## 구조 참고

- 도메인 디렉터리 규칙: `app/domain/<name>/{api,repo,schema,usecase}/`
- 새 모델 추가 시 `app/model/__init__.py`에 export 필수 (Alembic autogen 인식용)
- 라우터 include는 `app/main.py`의 `APP_SERVICE` 분기 TODO 위치
