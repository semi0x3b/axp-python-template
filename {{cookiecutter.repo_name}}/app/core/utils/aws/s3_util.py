"""AWS S3 비동기 유틸리티

공통 S3 읽기/쓰기 기능을 제공합니다.
"""

import json
from functools import lru_cache
from typing import Any, Dict, Optional, Union

import aioboto3
import structlog

logger = structlog.get_logger()


@lru_cache(maxsize=1)
def _shared_session() -> aioboto3.Session:
    """aioboto3 Session 은 프로세스에서 하나만 만든다 (인스턴스마다 생성 금지)."""
    return aioboto3.Session()


class AsyncS3Client:
    """비동기 S3 클라이언트

    aioboto3를 사용한 비동기 S3 작업을 제공합니다.

    Example:
        ```python
        s3_client = AsyncS3Client(bucket_name="my-bucket")

        # JSON 저장
        await s3_client.put_json("path/to/file.json", {"key": "value"})

        # JSON 읽기
        data = await s3_client.get_json("path/to/file.json")

        # 바이너리 저장/읽기
        await s3_client.put_object("path/to/file.bin", b"binary data")
        content = await s3_client.get_object("path/to/file.bin")
        ```
    """

    def __init__(self, bucket_name: str, region_name: Optional[str] = None):
        """S3 클라이언트 초기화.

        Args:
            bucket_name: S3 버킷 이름
            region_name: AWS 리전 (기본값: boto3 기본 리전)
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._session = _shared_session()

    async def get_object(self, s3_key: str) -> Optional[bytes]:
        """S3에서 객체 읽기.

        Args:
            s3_key: S3 객체 키

        Returns:
            객체 내용 (바이트), 실패 시 None
        """
        try:
            async with self._session.client("s3", region_name=self.region_name) as client:
                response = await client.get_object(Bucket=self.bucket_name, Key=s3_key)
                body = await response["Body"].read()
                return body
        except Exception as e:
            logger.error(
                "s3_get_object_error",
                bucket=self.bucket_name,
                key=s3_key,
                error=str(e),
            )
            return None

    async def get_json(self, s3_key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """S3에서 JSON 객체 읽기.

        Args:
            s3_key: S3 객체 키
            default: 실패 시 반환할 기본값 (기본: 빈 딕셔너리)

        Returns:
            파싱된 JSON 데이터
        """
        if default is None:
            default = {}

        content = await self.get_object(s3_key)
        if content is None:
            return default

        try:
            return json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(
                "s3_json_parse_error",
                bucket=self.bucket_name,
                key=s3_key,
                error=str(e),
            )
            return default

    async def put_object(
        self,
        s3_key: str,
        body: Union[bytes, str],
        content_type: str = "application/octet-stream",
    ) -> bool:
        """S3에 객체 저장.

        Args:
            s3_key: S3 객체 키
            body: 저장할 내용 (바이트 또는 문자열)
            content_type: 콘텐츠 타입

        Returns:
            성공 여부
        """
        try:
            if isinstance(body, str):
                body = body.encode("utf-8")

            async with self._session.client("s3", region_name=self.region_name) as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=body,
                    ContentType=content_type,
                )
            return True
        except Exception as e:
            logger.error(
                "s3_put_object_error",
                bucket=self.bucket_name,
                key=s3_key,
                error=str(e),
            )
            return False

    async def put_json(
        self,
        s3_key: str,
        data: Dict[str, Any],
        ensure_ascii: bool = False,
    ) -> bool:
        """S3에 JSON 객체 저장.

        Args:
            s3_key: S3 객체 키
            data: 저장할 JSON 데이터
            ensure_ascii: ASCII 인코딩 강제 여부 (기본: False)

        Returns:
            성공 여부
        """
        try:
            body = json.dumps(data, ensure_ascii=ensure_ascii)
            return await self.put_object(
                s3_key=s3_key,
                body=body,
                content_type="application/json",
            )
        except (TypeError, ValueError) as e:
            logger.error(
                "s3_json_serialize_error",
                bucket=self.bucket_name,
                key=s3_key,
                error=str(e),
            )
            return False

    async def exists(self, s3_key: str) -> bool:
        """S3 객체 존재 여부 확인.

        Args:
            s3_key: S3 객체 키

        Returns:
            존재 여부
        """
        try:
            async with self._session.client("s3", region_name=self.region_name) as client:
                await client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
        except Exception:
            return False

    async def delete(self, s3_key: str) -> bool:
        """S3 객체 삭제.

        Args:
            s3_key: S3 객체 키

        Returns:
            성공 여부
        """
        try:
            async with self._session.client("s3", region_name=self.region_name) as client:
                await client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                return True
        except Exception as e:
            logger.error(
                "s3_delete_object_error",
                bucket=self.bucket_name,
                key=s3_key,
                error=str(e),
            )
            return False

    async def list_objects(self, prefix: str, max_keys: int = 1000) -> list[str]:
        """S3 객체 목록 조회.

        Args:
            prefix: 조회할 경로 prefix
            max_keys: 최대 반환 개수

        Returns:
            객체 키 목록
        """
        try:
            async with self._session.client("s3", region_name=self.region_name) as client:
                response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys,
                )
                contents = response.get("Contents", [])
                return [obj["Key"] for obj in contents]
        except Exception as e:
            logger.error(
                "s3_list_objects_error",
                bucket=self.bucket_name,
                prefix=prefix,
                error=str(e),
            )
            return []
