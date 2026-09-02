SHELL := /bin/bash

# bumpversion 플래그 토글 (DIRTY=1, DRY=1 로 제어)
BUMP_FLAGS :=
ifdef DIRTY
BUMP_FLAGS += --allow-dirty
endif
ifdef DRY
BUMP_FLAGS += --dry-run --verbose
endif

.PHONY: help
help:
	@echo "사용법:"
	@echo "  make dev                           # 로컬 개발 서버 (uvicorn --reload)"
	@echo "  make up                            # docker compose 기동"
	@echo "  make down                          # docker compose 종료"
	@echo "  make migrate                       # alembic upgrade head"
	@echo "  make revision MSG=\"...\"            # alembic autogenerate revision"
	@echo "  make test                          # pytest 전체"
	@echo "  make test-unit                     # pytest tests/unit (DB 불필요)"
	@echo "  make lint                          # black ."
	@echo "  make typecheck                     # mypy"
	@echo ""
	@echo "  --- bumpversion ---"
	@echo "  make bump[-minor|-major]           # 루트 버전 (pyproject + APP_VERSION)"
	@echo "  make bump-svc SVC=job [PART=minor] # 서비스 버전 (SVC: {{cookiecutter.container_prefix}}|backoffice|job)"
	@echo "  (옵션) DIRTY=1 --allow-dirty, DRY=1 --dry-run --verbose"
	@echo ""
	@echo "  --- Job ---"
	@echo "  make job-run NAME=ping             # Job 1회 수동 실행"
	@echo "  make job-list                      # 등록된 Job 목록"

# ---------------- local dev ----------------
.PHONY: dev
dev:
	poetry run uvicorn app.asgi:app --reload --port 8000

.PHONY: up down
up:
	docker compose -f docker/docker-compose.yml up --build -d
down:
	docker compose -f docker/docker-compose.yml down

.PHONY: migrate
migrate:
	poetry run alembic upgrade head

.PHONY: revision
revision:
	poetry run alembic revision --autogenerate -m "$(MSG)"

.PHONY: test test-unit
test:
	poetry run pytest
test-unit:
	poetry run pytest tests/unit/ -q

.PHONY: lint
lint:
	poetry run black .

.PHONY: typecheck
typecheck:
	poetry run mypy app/ --ignore-missing-imports

# ---------------- job ----------------
.PHONY: job-run job-list

# make job-run NAME=ping
job-run:
	poetry run python -m app.cli job run $(NAME)

job-list:
	poetry run python -m app.cli job list

# ---------------- bumpversion ----------------
# 서비스별 cfg 를 나눠 배포 이미지마다 독립 버전을 매긴다.
# 새 서비스 추가 시 .bumpversion.{서비스}.cfg + app/domain/{서비스}/version.py 를 함께 만든다.
.PHONY: bump bump-minor bump-major
bump:
	bumpversion $(BUMP_FLAGS) patch
bump-minor:
	bumpversion $(BUMP_FLAGS) minor
bump-major:
	bumpversion $(BUMP_FLAGS) major

# make bump-svc SVC=job [PART=minor|major]  → .bumpversion.$(SVC).cfg 사용
.PHONY: bump-svc
bump-svc:
	@test -n "$(SVC)" || { echo "SVC=<서비스명> 이 필요합니다 (예: make bump-svc SVC=job)"; exit 1; }
	bumpversion $(BUMP_FLAGS) --config-file .bumpversion.$(SVC).cfg $(or $(PART),patch)
