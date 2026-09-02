---
description: Alembic 마이그레이션 리비전 생성 + upgrade 자동 실행
allowed-tools: Bash(poetry:*), Bash(grep:*), Bash(git:*), Bash(ls:*), Bash(cat:*)
---

## Context

- DB_HOST: !`grep '^DB_HOST=' .env | cut -d= -f2`
- 모델/마이그레이션 변경 파일: !`git diff --name-only HEAD -- 'app/model/*.py' 'migrations/versions/*.py'; git ls-files --others --exclude-standard -- 'app/model/*.py'`
- 최근 커밋 제목: !`git log --oneline -5`

---

## Your Task

Alembic 마이그레이션 리비전을 자동 생성하고 `upgrade head`까지 실행한다.

### Step 1: 안전 체크 (실패 시 즉시 중단)

1. **운영 DB 차단**: `.env`의 `DB_HOST`가 운영 DB 호스트면 중단하고 사용자에게 알림 (로컬·개발 DB는 허용). 운영 호스트 패턴은 프로젝트 세팅 시 여기에 명시한다.
2. **head 동기화 체크**:
   - `poetry run alembic current` 실행 → 현재 리비전 추출
   - `poetry run alembic heads` 실행 → head 목록
   - current가 heads와 일치하지 않으면 중단: "DB가 최신 head가 아닙니다. 먼저 `poetry run alembic upgrade head`를 실행하세요."
   - multiple heads(2개 이상)면 중단: "head가 여러 개입니다. merge revision이 필요합니다."

### Step 2: 메시지 자동 생성

`git diff --name-only HEAD` + untracked 파일에서 `app/model/*.py`와 도메인 변경을 파악하여 **영어 snake_case** 커밋 메시지 생성 (50자 이내).

원칙:
- 모델 파일명 + 주된 변경 동작 조합 (`add`, `rename`, `drop`, `rebuild`, `alter`)
- 예: `add notice_table`, `rename user_status column`, `drop legacy_files and add is_public to comn_file_uploads`
- 변경된 모델이 없고 최근 커밋 제목이 있으면 그걸 영어로 변환

### Step 3: 리비전 생성

```bash
poetry run alembic revision --autogenerate -m "<message>"
```

- 출력에서 생성된 파일 경로 파싱 (`migrations/versions/<hash>_<slug>.py`)
- 에러 발생 시 출력 그대로 보여주고 중단

### Step 4: 빈 리비전 검증

생성된 파일을 읽고 `upgrade()` 함수 본문이 `pass`만 있거나 실제 `op.*` 호출이 0개면:
- 파일 삭제 (`rm <path>`)
- 중단: "감지된 스키마 변경이 없습니다. 모델 변경을 먼저 적용하거나 수동 리비전이 필요합니다."

### Step 5: 변경 요약 출력

생성 파일에서 다음 카운트 추출하여 한 줄 요약:
- `op.create_table`, `op.drop_table`
- `op.add_column`, `op.drop_column`, `op.alter_column`
- `op.create_index`, `op.drop_index`
- `op.create_foreign_key`, `op.drop_constraint`

형식:
```
📄 <파일경로>
📊 +N tables, -N tables | +N columns, -N columns, ~N altered | +N indexes, -N indexes
```

### Step 6: upgrade 실행

```bash
poetry run alembic upgrade head
```

- 성공 시: `✅ upgrade head 완료 (<새 리비전 hash>)` 출력
- 실패 시: 에러 출력 + "생성된 파일은 유지됩니다. 수정 후 다시 `poetry run alembic upgrade head` 실행하세요."

### Step 7: 마무리

- 변경된 파일 목록과 다음 단계 안내만 출력
- 커밋/푸시는 하지 않음 (사용자가 `/commit-message`로 직접 처리)

---

## 중단 규칙 요약

| 조건 | 동작 |
|------|------|
| DB_HOST가 운영 DB | 즉시 중단 |
| alembic current != heads | 중단, sync 먼저 안내 |
| multiple heads | 중단, merge 안내 |
| autogenerate 빈 리비전 | 파일 삭제 후 중단 |
| revision/upgrade 에러 | 출력 후 중단 |

## 주의사항

- `poetry run`을 항상 사용 (프로젝트는 Poetry 기반, `uv run` 사용 금지)
- 메시지는 영어, snake/공백 허용, 따옴표로 감싸서 전달
- 사용자에게 확인 묻지 않고 자동 진행 (안전 체크만 통과하면)
