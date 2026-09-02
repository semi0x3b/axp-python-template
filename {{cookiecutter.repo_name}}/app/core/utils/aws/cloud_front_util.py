"""AWS CloudFront 유틸리티."""

import uuid
from dataclasses import dataclass
from typing import Sequence

from app.core.config import settings
from app.core.logger import get_logger
from app.core.utils.aws.aws_service_util import AwsServiceUtil

logger = get_logger(__name__)


def build_file_url(file_path: str) -> str:
    """파일 경로로 파일 URL을 생성한다.

    CloudFront 도메인이 설정되어 있으면 CF URL, 아니면 file_path 그대로 반환.
    """
    if settings.CLOUDFRONT_DOMAIN:
        return f"https://{settings.CLOUDFRONT_DOMAIN}/{file_path}"
    return file_path


@dataclass
class CloudFrontUtil(AwsServiceUtil):
    """CloudFront 캐시 무효화."""

    def create_invalidation(
        self,
        distribution_id: str,
        paths: Sequence[str],
    ) -> dict:
        """CloudFront 캐시 무효화 요청을 생성한다.

        Args:
            distribution_id: CloudFront 배포 ID.
            paths: 무효화할 경로 목록 (예: ["/posts/images/*"]).

        Returns:
            CloudFront API 응답.

        Raises:
            ValueError: paths가 비어있는 경우.
        """
        if not paths:
            raise ValueError("paths must not be empty")

        caller_reference = f"invalidation-{uuid.uuid4()}"

        response = self.client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                "Paths": {
                    "Quantity": len(paths),
                    "Items": list(paths),
                },
                "CallerReference": caller_reference,
            },
        )

        logger.info(
            "cloudfront_invalidation_created",
            distribution_id=distribution_id,
            paths=list(paths),
            caller_reference=caller_reference,
        )
        return response
