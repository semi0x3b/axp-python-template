# 테스트 실행

프로젝트의 테스트를 실행하고 결과를 분석합니다.

## 실행 대상

- 사용자가 파일/패턴을 지정한 경우: `$ARGUMENTS`
- 지정하지 않은 경우: 전체 테스트 실행

## 1. 테스트 유형별 실행

### 전체 테스트
```bash
poetry run pytest -v
```

### 단위 테스트만
```bash
poetry run pytest tests/unit/ -v
```

### 통합 테스트만
```bash
poetry run pytest tests/integration/ -v
```

### 특정 도메인 테스트
```bash
poetry run pytest -k "board" -v       # 게시판 관련
poetry run pytest -k "auth" -v        # 인증 관련
poetry run pytest -k "report" -v      # 신고 관련
```

## 2. 세부 실행 옵션

### 특정 파일
```bash
poetry run pytest tests/unit/test_board_api.py -v
```

### 특정 클래스
```bash
poetry run pytest tests/unit/test_board_api.py::TestBoardAPI -v
```

### 특정 함수
```bash
poetry run pytest tests/unit/test_board_api.py::TestBoardAPI::test_create_success -v
```

### 패턴 매칭
```bash
poetry run pytest -k "test_create and not validation" -v
```

## 3. 커버리지 리포트

```bash
# 터미널 출력
poetry run pytest --cov=app --cov-report=term

# HTML 리포트 (htmlcov/ 생성)
poetry run pytest --cov=app --cov-report=html

# 특정 도메인만
poetry run pytest --cov=app/domain --cov-report=term
```

## 4. 실행 옵션

| 옵션 | 설명 |
|------|------|
| `-v` | 상세 출력 |
| `-x` | 첫 실패 시 중단 |
| `-s` | print 출력 표시 |
| `--tb=short` | 간단한 스택트레이스 |
| `--tb=long` | 상세한 스택트레이스 |

## 5. 결과 분석

테스트 실행 후 확인:
- 통과/실패 테스트 수
- 실패한 테스트의 원인 분석
- 커버리지 퍼센트 (요청 시)

## 6. 실패 시 대응

테스트 실패 시:
1. 에러 메시지 분석
2. 원인 파악 (코드 버그 / 테스트 오류)
3. 수정 방안 제시
4. 필요 시 코드 또는 테스트 수정

## 출력 형식

```
## 테스트 실행 결과

**유형**: 단위 / 통합 / 전체

- 전체: N개
- 통과: N개
- 실패: N개
- 스킵: N개

## 실패 테스트 (있는 경우)

### test_xxx_xxx
- 파일: tests/unit/test_xxx.py:123
- 원인: ...
- 수정 방안: ...

## 커버리지 (요청 시)
- 전체: XX%
- app/domain: XX%
```

## 참고 자료

- `.claude/CLAUDE.md`: 테스트 규칙 및 컨벤션
- `tests/conftest.py`: 공통 fixture
- `pyproject.toml`: pytest 설정
