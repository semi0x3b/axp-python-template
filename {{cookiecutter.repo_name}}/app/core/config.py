"""애플리케이션 환경 설정.

설정값 분류 원칙:
  - .env / Secrets Manager: 환경별로 달라지거나 보안이 필요한 값
  - 코드 직접 설정: 환경에 관계없이 고정된 값
  - 파생값: ENVIRONMENT로부터 자동 결정되는 값

.env 파일 로딩 전략:
  1. USE_ENV_FILE 환경 변수로 명시적 제어 (최우선)
  2. ENVIRONMENT가 미설정 또는 "local"이면 .env 파일 사용 (로컬 개발)
  3. 운영 환경(dev/prod)에서는 .env 파일 사용 안 함 → AWS Secrets Manager 사용

Settings Sources 우선순위 (높음 → 낮음):
  1. init_settings: 직접 전달된 초기화 인자
  2. env_settings: OS 환경 변수
  3. dotenv_settings: .env 파일
  4. AWSSecretsSource: AWS Secrets Manager
  5. file_secret_settings: 파일 기반 시크릿
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from app.core.enum.environment import Environment

# ── .env 파일 사용 여부 결정 ──
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

USE_ENV_FILE_ENV = os.getenv("USE_ENV_FILE")
ENVIRONMENT_ENV = os.getenv("ENVIRONMENT", "").lower()

if USE_ENV_FILE_ENV is not None:
    USE_ENV_FILE = USE_ENV_FILE_ENV.lower() == "true"
else:
    USE_ENV_FILE = not ENVIRONMENT_ENV or ENVIRONMENT_ENV == "local"

ENV_FILE = str(ENV_FILE_PATH) if USE_ENV_FILE and ENV_FILE_PATH.exists() else None

# ── 시스템 봇 계정 ──
BOT_USER_PUBLIC_ID = "00000000-0000-0000-0000-000000000001"

# ── 보안 키 코드 기본값 (= "주입되지 않음" 표식) ──
# 운영(dev/prod)에서 이 값이 그대로 남아 있으면 부팅을 거부한다.
# local 은 개발 편의를 위해 허용.
INSECURE_JWT_SECRET_DEFAULT = "change-me-in-production"
INSECURE_ENCRYPTION_KEY_DEFAULT = "0" * 64


class AWSSecretsSource(PydanticBaseSettingsSource):
    """AWS Secrets Manager를 settings source로 사용."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """AWS Secrets Manager에서 모든 설정 값 로드."""
        environment = os.getenv("ENVIRONMENT", "").lower()
        if not environment or environment == "local":
            return {}

        secret_name = os.getenv("AWS_SECRET_NAME")
        if not secret_name:
            if environment == "prod":
                secret_name = "{{cookiecutter.aws_secret_prefix}}-prod-env"
            else:
                secret_name = "{{cookiecutter.aws_secret_prefix}}-dev-env"

        try:
            from app.core.utils.aws.secret_manager_util import get_secret_manager

            aws_region = os.getenv("AWS_REGION", "ap-northeast-2")
            secret_manager = get_secret_manager(region_name=aws_region)
            secrets_dict = secret_manager.get_secret(secret_name)

            if secrets_dict:
                print(f"✅ Loaded {len(secrets_dict)} secrets from AWS Secret Manager: {secret_name}")
                return secrets_dict

            print(f"⚠️  Failed to load secrets from AWS Secret Manager: {secret_name}")
            return {}

        except ImportError as e:
            print(f"⚠️  Secret Manager utilities not available: {e}")
            return {}
        except Exception as e:
            print(f"⚠️  Failed to load secrets from AWS Secret Manager: {e}")
            return {}


class Settings(BaseSettings):
    """애플리케이션 환경 설정."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            AWSSecretsSource(settings_cls),
            file_secret_settings,
        )

    # ══════════ .env에서 로드 (환경별 상이 / 보안 필요) ══════════

    ENVIRONMENT: Environment = Field(default=Environment.local)

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: Any) -> str:
        """ENVIRONMENT 값 정규화 (develop → dev)."""
        if isinstance(v, str) and v.lower() == "develop":
            return "dev"
        return v

    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="postgres")
    DB_NAME: str = Field(default="{{cookiecutter.db_name}}")

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")

    REDIS_CHAT_DB: int = Field(default=1)

    JWT_SECRET_KEY: str = Field(default=INSECURE_JWT_SECRET_DEFAULT)
    ENCRYPTION_KEY: str = Field(default=INSECURE_ENCRYPTION_KEY_DEFAULT)  # AES-256용 32바이트 hex 문자열

    ALLOWED_ORIGINS: list[str] = Field(default=["*"])

    # AWS S3 / CloudFront
    AWS_REGION: str = Field(default="ap-northeast-2")
    S3_BUCKET_NAME: str = Field(default="")
    CLOUDFRONT_DOMAIN: str = Field(default="")
    CLOUDFRONT_DISTRIBUTION_ID: str = Field(default="")

    # Swagger Basic Auth (비밀번호 미설정 시 인증 미적용)
    SWAGGER_USERNAME: str = Field(default="admin")
    SWAGGER_PASSWORD: str = Field(default="")

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """AES-256 키 포맷 검증 (환경 무관) — 64자 hex 문자열."""
        try:
            raw = bytes.fromhex(v)
        except ValueError:
            raise ValueError("ENCRYPTION_KEY must be a hex string")
        if len(raw) != 32:
            raise ValueError("ENCRYPTION_KEY must decode to 32 bytes (64 hex chars)")
        return v

    @model_validator(mode="after")
    def reject_insecure_defaults_in_deployed_env(self) -> "Settings":
        """운영(dev/prod)에서 보안 키가 코드 기본값이면 부팅 거부.

        키를 주입하지 않은 채 배포되어 토큰 위조·복호화가 뚫리는 사고를 막는다.
        """
        if self.ENVIRONMENT == Environment.local:
            return self

        missing = []
        if self.JWT_SECRET_KEY == INSECURE_JWT_SECRET_DEFAULT:
            missing.append("JWT_SECRET_KEY")
        if self.ENCRYPTION_KEY == INSECURE_ENCRYPTION_KEY_DEFAULT:
            missing.append("ENCRYPTION_KEY")
        if missing:
            raise ValueError(f"{self.ENVIRONMENT.value} 환경에서 보안 키가 코드 기본값입니다: {', '.join(missing)}")
        return self

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        """ALLOWED_ORIGINS 파싱 (JSON, 쉼표 구분, 단일 값)."""
        if v is None:
            return ["*"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return ["*"]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            if "," in v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            return [v.strip()] if v.strip() else ["*"]
        return ["*"]

    # ══════════ 고정값 (코드에서 직접 설정, 환경 무관) ══════════

    APP_TITLE: str = "{{cookiecutter.project_name}} API"
    APP_VERSION: str = "0.0.1"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_MAIN_NAME: str = "main"
    REDIS_CHAT_NAME: str = "chat"

    # ══════════ 파생값 (ENVIRONMENT로부터 자동 결정) ══════════

    @property
    def DEBUG(self) -> bool:
        """local 환경에서만 True."""
        return self.ENVIRONMENT == Environment.local

    @property
    def LOG_LEVEL(self) -> str:
        """local → DEBUG, 운영 → INFO."""
        return "DEBUG" if self.ENVIRONMENT == Environment.local else "INFO"

    @property
    def access_token_expire_minutes(self) -> int:
        """local/dev → 24시간, 운영 → 설정값(30분)."""
        if self.ENVIRONMENT in (Environment.local, Environment.development):
            return 1440
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    # ══════════ URL 프로퍼티 ══════════

    @property
    def database_url(self) -> str:
        """비동기 DB URL (SQLAlchemy AsyncEngine용)."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_database_url(self) -> str:
        """동기 DB URL (Alembic migration용)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_password_or_none(self) -> str | None:
        """비밀번호가 빈 문자열이면 None 반환 (로컬 개발용)."""
        return self.REDIS_PASSWORD or None

    @property
    def redis_url(self) -> str:
        """Redis 접속 URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def redis_chat_url(self) -> str:
        """채팅 전용 Redis 접속 URL (같은 서버, 다른 DB)."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_CHAT_DB}"


settings = Settings()
