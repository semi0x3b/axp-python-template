# {{cookiecutter.project_name}}

{{cookiecutter.project_description}}

## 기술 스택

- Python {{cookiecutter.python_version}}
- FastAPI
- SQLAlchemy 2.0 (Async)
- PostgreSQL + asyncpg
- Redis
- Alembic (마이그레이션)

## 시작하기

### 의존성 설치

```bash
poetry install
```

### 환경 설정

```bash
cp .env.example .env
# .env 파일을 환경에 맞게 수정
```

### 서버 실행

```bash
poetry run uvicorn app.asgi:app --reload --port 8000
```

### pre-commit 훅 설치

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
```

커밋 시 black 자동 포맷 + 변경분 단위 테스트, push 시 단위 테스트 전체가 돈다.
`migration` 브랜치에서는 전부 skip 된다.

### 테스트

```bash
make test-unit   # tests/unit — DB 불필요
make test        # 전체 (통합 테스트는 make up 으로 db-test:5433 기동 필요)
```

`tests/conftest.py` 가 테스트용 env 기본값을 주입하므로 `.env` 없이도 실행된다.

### 포맷팅

```bash
poetry run black .
```

### 타입 체크

```bash
poetry run mypy app/ --ignore-missing-imports
```

## 버전 관리

서비스(배포 이미지)별로 독립 버전을 매긴다.

```bash
make bump[-minor|-major]     # 루트 버전 (pyproject + APP_VERSION)
make bump-svc SVC=job [PART=minor|major]   # 서비스 버전 (SVC: {{cookiecutter.container_prefix}}|backoffice|job)
#   DIRTY=1 → --allow-dirty, DRY=1 → --dry-run --verbose
```

새 서비스 추가 시 `.bumpversion.{서비스}.cfg` + `app/domain/{서비스}/version.py` 를 만들고 `build-on-main.yml` 의 `SERVICES` 에 추가한다.

`main` 과 `develop` 양쪽에서 bump 되어 버전 줄이 충돌하는 문제는
`.gitattributes` + `.github/merge-drivers/version-merge.py` 가 semver 높은 쪽을 골라 자동 해결한다.
드라이버는 프로젝트 생성 시 로컬 git config 에 등록되며, 등록 실패해도 기본 text 머지로 폴백한다.

## CI/CD

`.github/workflows/ci.yml` — PR 과 main/develop push 마다 `black --check` + `pytest`. 테스트 DB 는 워크플로 service 컨테이너(postgres, 5433) 로 띄워 `tests/conftest.py` 기본값 그대로 돈다.

`.github/workflows/build-on-main.yml` — `app/domain/<svc>/version.py` 가 바뀐 채 `main` 에 push 되면 그 서비스만 이미지 빌드 → 레지스트리 푸시 → gitops 레포의 prod overlay `newTag` 갱신 → Slack. ArgoCD 가 gitops 변경을 sync 하면 배포된다. 레지스트리는 생성 시 `registry` 옵션(ocir|ecr)으로 정해지며 워크플로 `REGISTRY_TYPE` 으로 바꿀 수 있다.

```
make bump-svc SVC=<svc> → main push → build-on-main → 레지스트리(OCIR|ECR) → gitops newTag → ArgoCD sync
```

시크릿: OCIR 은 `REGISTRY_USERNAME` / `REGISTRY_PASSWORD`, ECR 은 `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`(ECR 리포지토리는 없으면 자동 생성). 공통 `GITOPS_ACCESS_TOKEN` / `SLACK_BOT_TOKEN`(선택). 레지스트리·gitops 경로는 워크플로 상단 `env` 블록에서 바꾼다.

dev/prod 환경변수는 gitops 가 아니라 OCI Vault 에 있다 — 새 설정 키를 추가했으면 Vault 에도 넣는다.

## 브랜치 전략

- `main` — 배포. push 시 `sync-main-to-branches.yml` 이 `develop`·`migration` 으로 자동 머지
- `develop` — 개발 통합
- `migration` — 모델·마이그레이션 전용 (`/commit-message` 가 자동 분리)
- 충돌 시 force 하지 않고 수동 해결용 sync PR 을 연다

## 컨벤션

`.claude/` 에 레이어별 규칙이 있다. 코드 작성 전 확인하고, 작업 후 `/check-convention` 으로 검사한다.

| 문서 | 내용 |
|------|------|
| `.claude/CLAUDE.md` | 절대 금지·필수 패턴 |
| `.claude/rules/{api,usecase,repo,schema,model}.md` | 레이어별 세부 규칙 (해당 파일 Read 시 자동 로드) |
| `.claude/projects/CONVENTIONS.md` | 폴더 구조·레이어 요약 |
| `.claude/projects/OVERVIEW.md` | 테이블·API·env 스냅샷 (코드 변경 시 동시 갱신) |
| `.claude/projects/GLOSSARY.md` | 도메인 용어 — 새 식별자 만들기 전 확인 |
| `.claude/commands/` | `/check-convention` `/migrate` `/commit-message` `/commit` `/wt-commit` `/run-test` `/generate-test` `/update-overview` `/work-summary` `/context-subagent` |
| `.claude/commands/write-pr-description.md` | 커밋된 diff 기반 PR 본문(작업 내용/체크리스트) 작성 + PR 생성 |
| `.claude/agents/` | `domain-lead`(라우팅·온보딩) + `<domain>-expert`(도메인별 구현, 템플릿 `user-expert.md`) |

## 서비스 구성

| 서비스 | 설명 | 실행 방식 |
|--------|------|-----------|
| `{{cookiecutter.container_prefix}}` | {{cookiecutter.project_name}} | FastAPI (Uvicorn) |
| `backoffice` | 관리자 백오피스 API | FastAPI (Uvicorn) |
| `job` | 배치 스케줄러 | APScheduler 데몬 |

`APP_SERVICE` 환경변수로 로드할 서비스를 제어한다.

## Docker (로컬 개발)

```bash
make up    # PostgreSQL + Redis + API 서버 실행
make down  # 종료
```

## 프로젝트 구조

```
app/
├── main.py              # FastAPI 앱 팩토리
├── asgi.py              # ASGI 진입점
├── cli.py               # CLI 엔트리포인트
├── core/                # 공통 인프라
│   ├── base_model.py    # SQLAlchemy Base 클래스
│   ├── base_repository.py
│   ├── config.py
│   ├── enum/
│   ├── exception/
│   ├── middleware/
│   ├── schema/
│   ├── security/        # JWT, 비밀번호, 인증 의존성
│   ├── utils/
│   └── websocket/
├── db/
│   ├── base.py
│   └── connection.py
├── model/               # SQLAlchemy 모델
└── domain/              # 서비스별 → 도메인별 api/repo/schema/usecase
    ├── {{cookiecutter.container_prefix}}/
    ├── backoffice/
    └── job/

tests/
├── conftest.py          # 공용 픽스처 (test_engine / session / clean_db / *_client)
└── unit/                # DB 불필요 단위·계약 테스트

http/                    # IntelliJ HTTP Client 요청 모음 (http-client.env.json 참조)
```

도메인 폴더 상세 규칙은 `.claude/projects/CONVENTIONS.md` 참조.
