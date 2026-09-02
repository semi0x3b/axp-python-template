"""파일 업로드 관련 Enum."""

from enum import Enum


class FileAccessType(str, Enum):
    """파일 접근 유형."""

    CF = "cf"  # CloudFront 기반 퍼블릭 접근
    PS = "ps"  # Presigned URL 기반 프라이빗 접근


class FileExtension(str, Enum):
    """허용 파일 확장자."""

    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    PDF = "pdf"
    ZIP = "zip"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    MP4 = "mp4"
    MOV = "mov"

    @classmethod
    def image_extensions(cls) -> list["FileExtension"]:
        """이미지 확장자 목록을 반환한다."""
        return [cls.JPEG, cls.JPG, cls.PNG, cls.GIF, cls.WEBP]

    @classmethod
    def is_allowed(cls, ext: str) -> bool:
        """허용된 확장자인지 확인한다."""
        return ext.lower().lstrip(".") in [e.value for e in cls]


class UploadFileType(str, Enum):
    """업로드 파일 유형 — 도메인별 참조 정보를 반환한다."""

    POST_FILE = "post_file"
    PROFILE_IMAGE = "profile_image"

    def get_ref_type(self) -> str:
        """참조 테이블명을 반환한다."""
        mapping = {
            "post_file": "post_posts",
            "profile_image": "user_users",
        }
        return mapping.get(self.value, "")

    def get_key(self) -> str:
        """참조 테이블의 PK 컬럼명을 반환한다."""
        mapping = {
            "post_file": "post_id",
            "profile_image": "user_id",
        }
        return mapping.get(self.value, "")

    def get_s3_prefix(self) -> str:
        """S3 저장 경로 prefix를 반환한다."""
        mapping = {
            "post_file": "posts/files",
            "profile_image": "users/profiles",
        }
        return mapping.get(self.value, "uploads")
