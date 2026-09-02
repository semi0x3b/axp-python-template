"""S3 Presigned URL 생성 유틸리티.

Presigned URL 생성은 로컬 서명만 수행하므로 동기(boto3)로 충분하다.
실제 S3 객체 조작(get/put/delete)은 s3_util.py의 AsyncS3Client를 사용한다.
"""

import uuid
from dataclasses import dataclass, field
from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=None)
def _s3_client(region_name: str):
    """boto3 클라이언트는 region 별로 프로세스에서 하나만 만든다 (요청마다 생성 금지)."""
    return boto3.client(
        "s3",
        region_name=region_name,
        config=Config(s3={"addressing_style": "virtual"}),
    )


@dataclass
class S3PresignedUtil:
    """S3 Presigned URL 생성 유틸."""

    bucket_name: str
    region_name: str = "ap-northeast-2"
    _client: any = field(init=False, repr=False)

    def __post_init__(self):
        self._client = _s3_client(self.region_name)

    def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> dict[str, str | int]:
        """PUT용 Presigned URL을 생성한다.

        Args:
            s3_key: S3 객체 키 (저장 경로).
            content_type: 파일 Content-Type.
            expires_in: URL 만료 시간 (초, 기본 3600).

        Returns:
            upload_url, s3_key, expires_in을 포함한 딕셔너리.
        """
        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        logger.info("presigned_url_generated", s3_key=s3_key, expires_in=expires_in)
        return {
            "upload_url": url,
            "s3_key": s3_key,
            "expires_in": expires_in,
        }

    @staticmethod
    def generate_s3_key(prefix: str, original_filename: str) -> str:
        """UUID 기반 S3 키를 생성한다.

        Args:
            prefix: S3 경로 prefix (예: "posts/images").
            original_filename: 원본 파일명.

        Returns:
            S3 키 (예: "posts/images/550e8400-e29b-41d4-a716-446655440000.jpg").
        """
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        unique_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
        return f"{prefix}/{unique_name}"
