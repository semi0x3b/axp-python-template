"""운영 환경 보안 키 안전장치(config) 단위 테스트.

- 운영(dev/prod)에서 보안 키가 코드 기본값이면 부팅 거부
- local은 안전장치 미적용 (개발 편의)
- ENCRYPTION_KEY는 환경 무관 AES-256 hex(64자) 포맷 검증

실제 .env를 읽지 않도록 모든 인스턴스화에 _env_file=None을 넘긴다.
"""

import pytest

from app.core.config import (
    INSECURE_ENCRYPTION_KEY_DEFAULT,
    INSECURE_JWT_SECRET_DEFAULT,
    Settings,
)

VALID_HEX_32 = "ab" * 32  # 64 hex chars = 32 bytes, all-zero가 아님


def _real_keys() -> dict[str, str]:
    return {"JWT_SECRET_KEY": "real-jwt-secret", "ENCRYPTION_KEY": VALID_HEX_32}


def _insecure_keys() -> dict[str, str]:
    """전부 코드 기본값(미주입 표식). conftest가 OS env를 주입하므로 init 인자로 명시한다."""
    return {"JWT_SECRET_KEY": INSECURE_JWT_SECRET_DEFAULT, "ENCRYPTION_KEY": INSECURE_ENCRYPTION_KEY_DEFAULT}


def test_local_allows_insecure_defaults():
    settings = Settings(_env_file=None, ENVIRONMENT="local", **_insecure_keys())

    assert settings.JWT_SECRET_KEY == INSECURE_JWT_SECRET_DEFAULT
    assert settings.ENCRYPTION_KEY == INSECURE_ENCRYPTION_KEY_DEFAULT


@pytest.mark.parametrize("environment", ["dev", "prod"])
def test_deployed_env_rejects_insecure_defaults(environment: str):
    with pytest.raises(ValueError) as exc:
        Settings(_env_file=None, ENVIRONMENT=environment, **_insecure_keys())

    message = str(exc.value)
    assert "JWT_SECRET_KEY" in message
    assert "ENCRYPTION_KEY" in message


def test_prod_with_real_keys_boots():
    settings = Settings(_env_file=None, ENVIRONMENT="prod", **_real_keys())

    assert settings.ENVIRONMENT.value == "prod"
    assert settings.ENCRYPTION_KEY == VALID_HEX_32


def test_prod_reports_only_missing_key():
    keys = _real_keys()
    keys["JWT_SECRET_KEY"] = INSECURE_JWT_SECRET_DEFAULT

    with pytest.raises(ValueError) as exc:
        Settings(_env_file=None, ENVIRONMENT="prod", **keys)

    message = str(exc.value)
    assert "JWT_SECRET_KEY" in message
    assert "ENCRYPTION_KEY" not in message


def test_encryption_key_must_be_hex():
    with pytest.raises(ValueError, match="hex"):
        Settings(_env_file=None, ENVIRONMENT="local", ENCRYPTION_KEY="zz" * 32)


def test_encryption_key_must_be_32_bytes():
    with pytest.raises(ValueError, match="32"):
        Settings(_env_file=None, ENVIRONMENT="local", ENCRYPTION_KEY="ab" * 16)
