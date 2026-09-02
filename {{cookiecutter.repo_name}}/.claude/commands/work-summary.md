---
description: 작업 내용 확인. "오늘 뭐 작업했지", "어제 작업 내용", "작업 요약", "뭐 바꿨지", "새로 작업한 거", "변경사항 정리해줘" 같은 요청에 사용. API 변경 목록 + 기능별 작업 요약 출력. 날짜 미지정 시 오늘, 특정 날짜/어제/그제 등도 지원. "프론트 전달용", "프론트에 전달", "프론트 공유" 포함 시 Slack/노션 붙여넣기 전용 포맷으로 출력.
allowed-tools: Bash(git:*), Grep, Read, Glob, Write
---

이 작업은 Agent tool로 sonnet 모델에 위임하여 실행한다. 아래 전체 내용을 Agent prompt로 전달하고, 결과를 그대로 사용자에게 출력한다.

## 모드 결정

사용자 요청을 분석하여 세 가지 모드 중 하나로 결정한다.

| 모드 | 트리거 예시 | 동작 |
|------|-----------|------|
| **커밋 해시** | "abc1234 커밋부터", "abc1234 이후" | 해당 커밋부터 HEAD까지 조회 |
| **증분** | "뭐 바꿨지", "새로 작업한 거", "추가된 거" | 커서 파일 이후 커밋만 조회 |
| **전체** | "오늘 작업 내용", "어제 작업한 거", 날짜 지정 | 해당 날짜 전체 조회 (커서 무시) |

## 커서 관리

커서 파일: `.claude/state/work-summary-cursor`

```
# 파일 내용 형식 (1줄)
<commit-hash>
```

### 커밋 해시 모드

사용자가 커밋 해시(7~40자 hex 문자열)를 직접 제공한 경우.

1. `git log <provided-hash>..HEAD` 범위로 조회
2. 실행 완료 후 → 최신 커밋 해시를 커서 파일에 저장

### 증분 모드

1. 커서 파일이 존재하면 → `git log <cursor-hash>..HEAD` 범위로 조회
2. 커서 파일이 없으면 → 오늘 날짜 기준 전체 모드로 폴백
3. 실행 완료 후 → 조회 범위의 최신 커밋 해시를 커서 파일에 저장

### 전체 모드

1. 날짜 범위로 조회 (커서 파일 무시)
2. 실행 완료 후 → 조회 범위의 최신 커밋 해시를 커서 파일에 저장

## 날짜 결정 (전체 모드)

- 사용자가 날짜를 명시하지 않으면 **오늘** 기준
- "어제", "그제", "이번 주", 특정 날짜 등 요청 시 해당 범위 적용
- 날짜 패턴을 grep으로 필터링한다 (예: `grep "2026-05-18"`). `--since`/`--until` 사용 금지 — 머지 커밋이 있는 DAG에서 순회를 일찍 끊어 커밋을 누락한다.
- 이번 주처럼 날짜 범위가 여러 날인 경우 `grep -E "2026-05-13|2026-05-14|..."` 형태로 OR 처리

## 작성자 필터

`git config user.email`로 현재 사용자 이메일을 확인하고, 모든 git log 명령에 `--author=<email>` 옵션을 추가하여 **본인 커밋만** 조회한다.

## 실행 절차

### 1단계: 커밋 목록 수집

**커밋 해시 모드:**
```bash
AUTHOR=$(git config user.email)
git log <provided-hash>..HEAD --author="$AUTHOR" --format="%H %ai %s"
```

**증분 모드:**
```bash
AUTHOR=$(git config user.email)
git log <cursor-hash>..HEAD --author="$AUTHOR" --format="%H %ai %s"
```

**전체 모드:**
```bash
AUTHOR=$(git config user.email)
# --since/--until 금지: 머지 커밋 DAG 순회를 일찍 끊음. grep으로 날짜 필터링.
git log --all --author="$AUTHOR" --format="%H %ai %s" | grep "$DATE_PATTERN"
```

MERGE 커밋(`🔀`)은 이후 모든 단계에서 건너뜀.

### 2단계: 커밋 유형별 파일 수집

각 커밋에 대해 변경된 `.py` 파일 수집:
```bash
git diff-tree --no-commit-id --name-only -r "$hash" -- '*.py'
```

커밋 유형별 처리 기준:

| 커밋 태그 | API 목록 포함 | 기타 섹션 |
|-----------|-------------|---------|
| FEAT | 전체 (신규/변경 모두) | 작업 요약 |
| FIX | 스키마(`_request_schema.py`, `_response_schema.py`) 변경 시만 API 변경으로 포함 | 작업 요약 |
| REFACTOR | API 파일·스키마 변경 시만 API 변경으로 포함 | 작업 요약 |
| UPDATE | FEAT와 동일 | 작업 요약 |
| TEST | API 목록 제외 | 테스트 커버리지 섹션에 별도 나열 |
| MIGRATION | API 목록 제외 | 작업 요약 |
| STYLE/CHORE/DOCS | API 목록 제외 | 작업 요약 (한 줄) |

### 3단계: API 파일 식별

변경된 파일 중 다음을 필터링:
- `*/api/*.py` — API 핸들러
- `*/schema/request/*.py` — 요청 스키마
- `*/schema/response/*.py` — 응답 스키마
- `*/usecase/*.py` — 비즈니스 로직 (필드 추가 확인용)
- `*/repo/*.py` — 저장소 (eager loading 등 변경 확인용)

### 4단계: API 경로 추출

변경된 API 파일마다:
1. `@router.(get|post|put|patch|delete)` 데코레이터에서 경로 추출
2. 라우터 prefix 확인 (해당 도메인의 `*_router.py`)
3. 전체 URL 경로 조합

### 5단계: 변경 내용 파악

각 API별로 `git diff <hash>^..<hash> -- <file>` 로 실제 diff 확인:
- **신규 API**: 새로 추가된 엔드포인트
- **변경 API**: 추가/삭제/수정된 필드를 구체적으로 기술

FIX/REFACTOR 커밋에서 스키마가 변경된 경우도 반드시 포함.

### 6단계: 결과 출력

사용자 요청에 "프론트 전달용", "프론트에 전달", "프론트 공유" 등이 포함된 경우 **Slack/노션 포맷**을 사용한다. 그 외에는 기본 마크다운 포맷을 사용한다.

#### 기본 마크다운 포맷

```
**신규**
* `METHOD /api/v1/path` — 설명

**변경**
* `METHOD /api/v1/path` — 변경 내용 (필드 단위로 구체적으로)

**테스트 커버리지 추가**
* 도메인명 — 테스트 대상 API 요약
```

#### Slack/노션 포맷 (프론트 전달용)

전체를 하나의 코드블록(``` ``` ```)으로 감싸서 출력한다. 내부 형식:

```
📡 API 변경 내역 (~ YYYY-MM-DD)

━━━━━━━━━━━━━━━━━━━━━━━━━
🆕 신규 API
━━━━━━━━━━━━━━━━━━━━━━━━━

METHOD /api/v1/path
• 설명
• 응답 필드: field1, field2, field3
• 에러: 조건 → HTTP 상태코드

━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 변경 API
━━━━━━━━━━━━━━━━━━━━━━━━━

METHOD /api/v1/path (기능명)
• 변경 내용
  - 기존: field: type
  - 변경: field: NewType

METHOD /api/v1/path (Request body 추가)
• { "field": type }  → 설명 (기본값: ...)

━━━━━━━━━━━━━━━━━━━━━━━━━
📎 참고: 공통 타입
━━━━━━━━━━━━━━━━━━━━━━━━━

FileInfo {
  "url": "https://...",
  "file_name": "example.png",
  "content_type": "image/png",
  "size": 12345
}
```

규칙:
- API 경로는 코드블록 없이 평문으로 표시
- 필드 변경은 `기존: → 변경:` before/after 형식
- Request body는 JSON 인라인으로 표기
- FileInfo 등 응답에 처음 등장하는 공통 타입은 하단 "참고" 섹션에 구조 정의 포함
- 변경 없는 섹션(신규/변경 중 하나)은 생략

### 7단계: 기능별 작업 요약

커밋 메시지와 변경 파일을 기반으로 기능 단위로 묶어 1줄 요약:

```
## 작업 요약
* 기능명: 한 줄 설명
```

관련 커밋이 여러 개여도 하나의 기능이면 한 줄로 합침.

### 8단계: 커서 갱신

조회 범위의 최신 커밋 해시를 `.claude/state/work-summary-cursor`에 저장:

```bash
echo "<latest-commit-hash>" > .claude/state/work-summary-cursor
```

## 주의사항

- FIX/REFACTOR 커밋도 스키마 변경이 있으면 API 변경 목록에 포함
- TEST 커밋은 "테스트 커버리지 추가" 섹션에 별도 나열 (API 목록에서는 제외)
- 마이그레이션·모델 파일은 API 목록에서 제외
- API 경로는 실제 라우터 prefix 조합한 전체 경로로 표시
- 조회 결과가 없으면 "마지막 확인 이후 새로운 작업이 없습니다" 출력
