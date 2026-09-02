"""파일 업로드 메타데이터 모델."""

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseIdModel, PublicIdMixin, SoftDeleteMixin


class FileUpload(BaseIdModel, SoftDeleteMixin, PublicIdMixin):
    """파일 업로드 메타데이터.

    다형성 참조(ref_type/key/value)를 통해 어떤 도메인 엔티티에도 연결할 수 있다.
    실제 파일은 S3에 저장되며, 이 테이블은 메타데이터만 관리한다.
    """

    __tablename__ = "comn_file_uploads"
    __table_args__ = (Index("ix_comn_file_uploads_ref", "ref_type", "key", "value", "is_active"),)

    # 참조 정보 (다형성 연결)
    ref_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="참조 테이블명 (예: post_posts)",
    )
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="참조 PK 컬럼명 (예: post_id)",
    )
    value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="참조 PK 값 (예: 42)",
    )

    # 파일 메타정보
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="원본 파일명",
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="S3 저장 파일명 (UUID 기반)",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="S3 전체 경로",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="파일 크기 (bytes)",
    )
    file_extension: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="파일 확장자",
    )

    # 상태
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="공개 여부",
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="다운로드 횟수",
    )
    upload_file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="업로드 파일 유형",
    )
