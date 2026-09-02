from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config


@lru_cache(maxsize=None)
def _boto3_client(service_name: str, region: Optional[str]):
    """boto3 클라이언트는 (서비스, 리전) 별로 프로세스에서 하나만 만든다 (요청마다 생성 금지)."""
    cfg = Config(
        retries={"max_attempts": 5, "mode": "standard"},
        read_timeout=10,
        connect_timeout=5,
    )
    return boto3.client(service_name, region_name=region, config=cfg)


@dataclass
class AwsServiceUtil:
    """AWS Service Util"""

    client: any
    service_name: str

    @classmethod
    def from_env(cls, service_name: str, *, region: Optional[str] = None):
        """환경 변수 기반으로 AWS 서비스 클라이언트를 생성합니다.

        Args:
            service_name (str): 생성할 AWS 서비스명 (예: 'cloudfront', 's3', 'ses').
            region (Optional[str], optional): AWS 리전명. 기본값은 None이며, boto3 기본 리전 설정을 따릅니다.

        Returns:
            AwsServiceUtil: 생성된 AWS 서비스 클라이언트를 포함한 AwsServiceUtil 인스턴스.
        """
        return cls(client=_boto3_client(service_name, region), service_name=service_name)
