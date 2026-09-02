"""Job 실행 이력 모델.

job_results: EventBridge → Lambda 태스크 실행 결과 기록
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseIdModel


class JobResult(BaseIdModel):
    """Job 실행 결과.

    각 태스크 실행의 시작/종료/상태/결과를 기록한다.
    """

    __tablename__ = "job_results"
    __table_args__ = (Index("ix_job_results_job_name_started", "job_name", "started_at"),)

    job_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Job 식별자 (e.g., expire-badges)")
    func: Mapped[str] = mapped_column(String(200), nullable=False, comment="태스크 함수명 (비정규화)")
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="함수 인자 (JSON)")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="STARTED / SUCCESS / FAILED")
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="태스크 반환값 (JSON)")
    error: Mapped[str | None] = mapped_column(Text, nullable=True, comment="에러 메시지")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="실행 시작 시각")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="실행 종료 시각")
