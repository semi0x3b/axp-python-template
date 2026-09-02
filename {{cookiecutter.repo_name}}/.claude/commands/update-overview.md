---
description: app/domain/.../api 라우터와 app/model을 스캔해 .claude/projects/OVERVIEW.md를 코드 기준으로 갱신. 코드와 스펙 drift 검출·보고.
argument-hint: [--dry-run]
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

## 호출 형태

```
/update-overview              # 자동 섹션 전부 갱신 + drift 보고
/update-overview --dry-run    # 변경 예정만 보고, 파일 수정 X
```

대상 파일: `.claude/projects/OVERVIEW.md`
스캔 대상: `app/domain/`, `app/model/`, `app/core/enum/`, `app/core/config.py`

CLAUDE.md 규약: **"코드 변경이 스펙과 어긋나면 OVERVIEW.md 동시 갱신."** 이 의무를 자동화한다.

---

## 핵심 원칙

1. **코드가 진실원.** OVERVIEW와 코드가 어긋나면 **코드 기준으로 OVERVIEW를 고친다.** 반대 방향 금지.
2. **수동 작성 설명 문장은 보존.** 자동 갱신 대상은 **테이블·표 형태의 섹션**만.
3. **시크릿·env 값 자체를 OVERVIEW에 노출하지 않는다.** 변수명만.
4. **drift 발견 시 자동 수정 + 변경 diff 요약 보고.**

---

## 자동 갱신 대상 섹션

OVERVIEW.md 내 다음 섹션을 코드 스캔으로 재생성·갱신.

### A. 테이블 맵 (`### user_`, `### admn_`, `### cmpn_`, ...)

소스: `app/model/__init__.py` + `app/model/{도메인}_model.py`

- 각 `__tablename__` 값을 prefix로 분류
- 클래스 docstring 또는 첫 클래스 코멘트의 한 줄을 "설명" 컬럼으로 사용
- 신규 모델 추가 → 표에 행 추가
- 모델 삭제 → 행 제거 + 변경 로그 기록

### B. API 표 (`### 3.x` 하위 표)

소스: `app/domain/{home|backoffice|common}/{도메인}/api/*.py` + 라우터 등록 파일

- `@router.get/post/patch/delete` 데코레이터에서 path 추출
- 인증 의존성으로 영역 분류:
  - `get_current_user` / `require_role(...)` → "사용자"
  - `get_current_admin` → "백오피스"
  - 인증 의존성 없음 → "공개"
- prefix 묶음: `/api/v1/`, `/api/v1/backoffice/`
- 표 컬럼: `경로` / `메서드` / `설명` (docstring `summary` 또는 함수 docstring 첫 줄)

### C. 에러코드 표

소스: `app/core/enum/response_message.py` (또는 유사 enum 파일)

- enum 값과 메시지를 표로 재생성

### D. ENV 변수 목록

소스: `app/core/config.py`

- `Settings` 클래스 필드명만 추출 (**값은 절대 노출 X**)
- 카테고리(DB / Redis / OCI / JWT / 외부 API 등)는 코멘트 기반 분류

### E. 배포 이미지·구조 표

코드에서 추출 불가 → **자동 갱신 제외**, 수동 영역 보존.

---

## Workflow

### Step 1. 현재 OVERVIEW.md 로드 + 섹션 경계 파싱

`<!-- AUTO:BEGIN section-name -->` ~ `<!-- AUTO:END section-name -->` 마커가 있으면 그 사이만 갱신.
마커가 없으면:
- 처음 실행 시: 자동 갱신 대상 섹션 식별 후 마커 후보 제시 → 사용자 확인 후 삽입.
- 이후: 마커 안만 갱신.

### Step 2. 코드 스캔

- 모델: `grep -rn "^class.*Base.*:" app/model/ | ...`
- 라우터: 글롭 `app/domain/**/api/*.py` Read 후 데코레이터 파싱
- enum: `app/core/enum/response_message.py` Read
- config: `app/core/config.py` Read

### Step 3. Diff 계산

기존 OVERVIEW 표의 행 vs 코드 추출 행:
- 신규 행 (코드에는 있고 OVERVIEW에는 없음)
- 삭제 행 (OVERVIEW에는 있고 코드에는 없음)
- 변경 행 (path/설명 등 변경)

### Step 4. 갱신

각 자동 섹션을 새로 작성한 표로 교체. 마커 바깥 텍스트는 절대 건드리지 않는다.
`--dry-run` 이면 갱신 적용 없이 diff만 보고.

### Step 5. 보고

```
## OVERVIEW 갱신 결과
- 테이블 맵: +N / -N / ~N
  - 추가: cmpn_jobs_documents
  - 변경: cmpn_jobs 설명 갱신
- API 표:
  - 구직자: +2 (`/api/v1/saved-jobs/*`)
  - 백오피스: +3 (`/api/v1/backoffice/jobs/{id}/approve` 등)
- 에러코드: +N
- ENV: +N (DB_REPLICA_URL)

## Drift 경고
- `/api/v1/companies/me` 가 OVERVIEW에는 GET만 있는데 코드에는 PATCH도 있음 → 추가
- `admn_audit_logs.target_type` 컬럼 — OVERVIEW 설명 없음 → 모델 docstring 추가 권장
```

---

## 절대 금지

- **수동 작성 설명 문장(섹션 도입부, 캐비엣 항목 등)을 임의 수정·삭제 X.** 자동 표 갱신만.
- **`.env`/Vault 값을 OVERVIEW에 적지 X.** 변수명만.
- **`<!-- AUTO:BEGIN/END -->` 마커를 사용자 허락 없이 추가 X.** 처음에는 후보 제시 후 확인.
- **GLOSSARY.md / CONVENTIONS.md / ARCHITECTURE.md 는 건드리지 X.** OVERVIEW만.
- **코드를 OVERVIEW에 맞추는 방향 변경 X.** 항상 코드 → OVERVIEW.

$ARGUMENTS
