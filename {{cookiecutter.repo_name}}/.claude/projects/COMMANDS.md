# 커맨드

```bash
make dev                     # uvicorn --reload, port 8000
make up / make down          # docker compose (docker/docker-compose.yml)
make migrate                 # alembic upgrade head
make revision MSG="..."      # alembic autogenerate revision
make test                    # pytest 전체
make lint                    # black .
make typecheck               # mypy app/

make job-run NAME=ping       # Job 1회 수동 실행
make job-list                # 등록된 Job 목록

make bump[-minor|-major]     # 루트 버전 (pyproject + APP_VERSION)
make bump-svc SVC=job [PART=minor|major]   # 서비스 버전 (SVC: {{cookiecutter.container_prefix}}|backoffice|job)
#   DIRTY=1 → --allow-dirty, DRY=1 → --dry-run --verbose
```

## 테스트

```bash
poetry run pytest tests/unit/ -q          # 단위 (DB 불필요)
poetry run pytest tests/integration/ -q   # 통합 (테스트 DB 필요: docker compose 5433)
```

`tests/conftest.py`가 테스트용 env 기본값을 주입하므로 `.env` 없이도 실행된다.
