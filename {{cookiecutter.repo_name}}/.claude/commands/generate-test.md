# 테스트 코드 생성

개발 완료된 코드에 대해 프로젝트의 테스트 규칙과 패턴에 맞는 테스트를 생성합니다.

## 0. 핵심 설정

```toml
# pyproject.toml
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
```

`asyncio_mode = "auto"` 설정으로 **`@pytest.mark.asyncio` 데코레이터가 불필요**. `async def test_...`만으로 자동 실행됨.

## 1. 대상 파일 분석

변경된 파일 또는 지정된 파일을 분석합니다:
- 사용자가 파일을 지정한 경우: `$ARGUMENTS`
- 지정하지 않은 경우: `git diff --name-only HEAD~1`로 최근 변경 파일 확인

## 2. 테스트 유형 및 위치

### 단위 테스트 (Unit Test)
외부 의존성을 Mock으로 대체하여 격리된 환경에서 테스트

| 파일 유형 | 테스트 위치 |
|----------|------------|
| `app/domain/**/api/*.py` | `tests/unit/test_{name}_api.py` |
| `app/domain/**/usecase/*.py` | `tests/unit/test_{name}_usecase.py` |
| `app/domain/**/repo/*.py` | `tests/unit/test_{name}_repo.py` |

### 통합 테스트 (Integration Test)
실제 DB 연결하여 전체 흐름 테스트

| 파일 유형 | 테스트 위치 |
|----------|------------|
| API 전체 흐름 | `tests/integration/test_{name}_integration.py` |
| DB 연동 | `tests/integration/test_{name}_integration.py` |

## 3. API 테스트 구조

`async_client` fixture는 `tests/conftest.py`에 정의됨. 별도 선언 불필요.

```python
"""{Name} API 단위 테스트."""

import uuid
import pytest
from app.core.security.jwt_handler import create_access_token


def _make_auth_headers(public_id: str | None = None) -> dict:
    """인증 헤더 생성 헬퍼. 인자는 app/core/security/jwt_handler.py 의 create_access_token 시그니처를 따른다."""
    token = create_access_token(public_id=public_id or str(uuid.uuid4()))
    return {"Authorization": f"Bearer {token}"}


class Test{Name}API:
    """정상 케이스."""

    endpoint = "/api/v1/{domain}/{resource}"

    async def test_{action}_success(self, async_client):
        """정상 요청 → 200."""
        response = await async_client.post(
            self.endpoint,
            json={...},
            headers=_make_auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] is not None


class Test{Name}APIValidation:
    """입력 검증 (422)."""

    async def test_missing_required_field_returns_422(self, async_client):
        """필수 필드 누락 → 422."""
        response = await async_client.post(
            "/api/v1/{domain}/{resource}", json={}, headers=_make_auth_headers()
        )
        assert response.status_code == 422


class Test{Name}APIAuth:
    """인증/인가 (401/403)."""

    async def test_no_token_returns_401(self, async_client):
        """토큰 없음 → 401."""
        response = await async_client.post("/api/v1/{domain}/{resource}", json={...})
        assert response.status_code == 401

    async def test_insufficient_role_returns_403(self, async_client):
        """권한 부족 → 403."""
        response = await async_client.post(
            "/api/v1/{domain}/{resource}",
            json={...},
            headers=_make_auth_headers(),
        )
        assert response.status_code == 403
```

## 4. UseCase 테스트 구조

> 본 프로젝트의 UseCase는 `AsyncSession`을 받아 내부에서 Repository를 생성하는 패턴.
> `repo=MagicMock()` 직접 주입이 아닌, **session mock + repo patch** 방식 사용.

```python
"""{Name}UseCase 단위 테스트."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception.handlers import ForbiddenError, NotFoundError


def _make_mock_{resource}(
    resource_id: int = 1,
    user_id: int = 1,
) -> MagicMock:
    """{Resource} mock 생성 헬퍼."""
    obj = MagicMock(spec=[])
    obj.id = resource_id
    obj.user_id = user_id
    return obj


class Test{Name}UseCase:
    """{Name}UseCase 단위 테스트."""

    @pytest.fixture
    def setup(self):
        """UseCase + mock repo 셋업. session 주입 → 내부 repo patch."""
        session = AsyncMock(spec=AsyncSession)
        with patch("app.domain.{service}.{domain}.usecase.{name}_usecase.{RepoClass}") as MockRepo:
            mock_repo = MagicMock()
            MockRepo.return_value = mock_repo
            usecase = {Name}UseCase(session)
        return usecase, mock_repo, session

    async def test_{method}_success(self, setup):
        """{조건} → {기대결과}."""
        usecase, mock_repo, _ = setup
        mock_repo.{method} = AsyncMock(return_value=_make_mock_{resource}())

        result = await usecase.{method}(...)

        assert result.id == 1
        mock_repo.{method}.assert_called_once()

    async def test_{method}_not_found_raises(self, setup):
        """존재하지 않는 리소스 → NotFoundError."""
        usecase, mock_repo, _ = setup
        mock_repo.{find_method} = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await usecase.{method}(...)

    async def test_{method}_forbidden_raises(self, setup):
        """권한 없는 사용자 → ForbiddenError."""
        usecase, mock_repo, _ = setup
        mock_obj = _make_mock_{resource}(user_id=999)  # 다른 사용자 소유
        mock_repo.{find_method} = AsyncMock(return_value=mock_obj)

        with pytest.raises(ForbiddenError):
            await usecase.{method}(user_id=1, ...)
```

### 복수 Repository UseCase (PostUseCase 등)

```python
@pytest.fixture
def setup(self):
    session = AsyncMock(spec=AsyncSession)
    with (
        patch("...post_usecase.PostRepo") as MockPostRepo,
        patch("...post_usecase.MenuRepo") as MockMenuRepo,
        patch("...post_usecase.MenuUseCase") as MockMenuUC,
        patch("...post_usecase.FileUploadRepo") as MockFileRepo,
    ):
        mock_post_repo = MagicMock()
        MockPostRepo.return_value = mock_post_repo
        mock_menu_repo = MagicMock()
        MockMenuRepo.return_value = mock_menu_repo
        mock_menu_uc = MagicMock()
        MockMenuUC.return_value = mock_menu_uc
        mock_file_repo = MagicMock()
        MockFileRepo.return_value = mock_file_repo
        usecase = PostUseCase(session)
    return usecase, mock_post_repo, mock_menu_repo, mock_menu_uc, mock_file_repo
```

## 5. Mock 패턴

### ORM 모델 Mock — `spec=[]` 필수

```python
from unittest.mock import MagicMock

# MagicMock 기본값은 속성 자동 생성 → ORM/Pydantic 검증 실패 가능
# spec=[]으로 자동 생성 방지 후 필요한 속성만 명시적으로 설정
user = MagicMock(spec=[])
user.id = 1
user.public_id = "uuid-string"
```

### UseCase Mock

```python
@pytest.fixture
def mock_post_usecase():
    mock = MagicMock()
    mock.create = AsyncMock(return_value=PostResponse(id=1, title="테스트"))
    return mock
```

### 외부 API Mock (patch)

```python
from unittest.mock import patch, AsyncMock

async def test_sms_send_success(self):
    """SMS 정상 발송 → True 반환."""
    with patch("app.core.utils.bizmsg.send_sms", new_callable=AsyncMock) as mock_sms:
        mock_sms.return_value = True
        result = await auth_usecase.send_verification_code("010-1234-5678")
        assert result is True
        mock_sms.assert_called_once()
```

## 6. 테스트 케이스 체크리스트

### 단위 테스트 (필수)
- [ ] 정상 요청 → 성공 응답
- [ ] 선택적 필드 없이 → 성공
- [ ] 필수 필드 누락 → 422
- [ ] 인증 실패 → 401
- [ ] 권한 부족 → 403
- [ ] 존재하지 않는 리소스 → 404
- [ ] 비즈니스 규칙 위반 → 400/409
- [ ] 엣지 케이스 (빈 값, 경계값)

### 통합 테스트 (선택 - 중요 기능)
- [ ] 실제 DB CRUD 흐름
- [ ] 트랜잭션 롤백 처리

## 7. 테스트 유형 선택 기준

| 상황 | 권장 테스트 |
|------|------------|
| 새 API 엔드포인트 | 단위 테스트 (필수) |
| DB 연동 로직 변경 | 단위 + 통합 테스트 |
| 핵심 비즈니스 로직 | 단위 + 통합 테스트 |
| 유틸리티 함수 | 단위 테스트만 |

## 8. 테스트 트러블슈팅

### ORM 모델 속성 오류

```python
# 문제: MagicMock 자동 생성 속성이 ORM/Pydantic 검증 실패
# 해결: spec=[]으로 자동 생성 방지
mock = MagicMock(spec=[])
mock.field = "명시적 값"
```

### 이벤트 루프 오류

```python
# 문제: RuntimeError: Event loop is closed
# 해결: pyproject.toml에 asyncio_default_fixture_loop_scope = "session" 설정됨
```

### UseCase 내부 Repo 패치 경로

```python
# Repo가 usecase 파일 내에서 임포트되는 경로를 정확히 지정해야 함
# 패턴: app.domain.{service}.{domain}.usecase.{name}_usecase.{RepoClass}
# 예시:
patch("app.domain.{service}.post.usecase.upvote_usecase.UpvoteRepository")
patch("app.domain.{service}.post.usecase.post_usecase.PostRepo")
```

## 참고 자료

- `tests/conftest.py`: 공통 fixture (`async_client`, `app`)
- `.claude/CLAUDE.md`: 프로젝트 테스트 컨벤션