---
description: Gitmoji 규칙으로 커밋 (템플릿 레포용 — 브랜치 동기화·migration 분리 없음)
allowed-tools: Bash(git:*)
---

## Context

- Status: !`git status --short`
- Branch: !`git rev-parse --abbrev-ref HEAD`
- Recent: !`git log --oneline -5`

## 규칙

`<emoji> <TAG>: <제목>` — 제목은 한글·명령형·50자 이내·마침표 없음. 본문은 선택("무엇을·왜").

| Emoji | TAG | 설명 |
|---|---|---|
| ✨ | FEAT | 새 기능 |
| 🐛 | FIX | 버그 수정 |
| 🔨 | UPDATE | 코드 수정 |
| 📝 | DOCS | 문서 |
| ♻️ | REFACTOR | 리팩토링 |
| 🧪 | TEST | 테스트 |
| 👷 | CI | CI/CD |
| 🔥 | REMOVE | 제거 |
| 📦 | DEPS | 의존성 |
| ⬆️ | CHORE | 빌드/설정 |
| 🚚 | MOVE | 이동/이름 변경 |

## 절차

1. 변경 파일을 논리 단위로 묶는다. 분리되면 커밋을 나눈다.
2. **`git add`는 이번 작업에서 만든·고친 파일만 명시** (`-A`·디렉터리 통짜 금지 — 병행 세션 작업물 혼입).
3. 커밋. `Co-Authored-By` 라인 넣지 않음. push는 사용자가 명시할 때만.
4. 생성 프로젝트 쪽(`{{cookiecutter.repo_name}}/`)을 건드렸으면 커밋 전에 렌더링 검증 1회:
   `cookiecutter . --no-input project_name=Demo output_parent=<scratch>` 후 `pytest tests/unit`.
