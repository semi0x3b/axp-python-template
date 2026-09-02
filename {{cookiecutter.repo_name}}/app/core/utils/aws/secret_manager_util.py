"""AWS Secret Manager 유틸리티."""

import json

import boto3
import structlog
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

logger = structlog.get_logger()


class SecretManagerUtil:
    """AWS Secret Manager에서 시크릿을 조회하는 유틸리티 클래스."""

    def __init__(self, region_name: str = "ap-northeast-2"):
        self.region_name = region_name
        self.client = None
        self.read_timeout = 5
        self.connect_timeout = 3

    def _get_client(self):
        """Boto3 Secret Manager 클라이언트 (지연 초기화)."""
        if self.client is None:
            config = Config(
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                retries={"max_attempts": 1},
            )
            session = boto3.session.Session()
            self.client = session.client(
                service_name="secretsmanager",
                region_name=self.region_name,
                config=config,
            )
        return self.client

    def get_secret(self, secret_name: str) -> dict | None:
        """Secret Manager에서 시크릿 조회.

        Args:
            secret_name: 시크릿 이름 (예: {{cookiecutter.aws_secret_prefix}}-dev-env)

        Returns:
            시크릿 딕셔너리 또는 None (실패 시)
        """
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                secret_dict = json.loads(response["SecretString"])
                logger.info("secret_loaded", secret_name=secret_name, num_keys=len(secret_dict))
                return secret_dict

            logger.warning("secret_binary_not_supported", secret_name=secret_name)
            return None

        except (ReadTimeoutError, ConnectTimeoutError) as e:
            logger.error("secret_manager_timeout", secret_name=secret_name, error_type=type(e).__name__, error=str(e))
            return None
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error("failed_to_load_secret", secret_name=secret_name, error_code=error_code, error=str(e))
            return None
        except json.JSONDecodeError as e:
            logger.error("failed_to_parse_secret_json", secret_name=secret_name, error=str(e))
            return None
        except Exception as e:
            logger.error(
                "unexpected_error_loading_secret",
                secret_name=secret_name,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
            return None


_secret_manager_instance: SecretManagerUtil | None = None
_secret_manager_lock = None


def get_secret_manager(region_name: str = "ap-northeast-2") -> SecretManagerUtil:
    """Secret Manager 유틸리티 싱글톤 인스턴스."""
    global _secret_manager_instance, _secret_manager_lock

    if _secret_manager_lock is None:
        import threading

        _secret_manager_lock = threading.Lock()

    if _secret_manager_instance is None:
        with _secret_manager_lock:
            if _secret_manager_instance is None:
                _secret_manager_instance = SecretManagerUtil(region_name=region_name)

    return _secret_manager_instance
