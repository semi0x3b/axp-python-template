"""Job 실행 결과 레포지토리."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.model.job import JobResult


class ResultRepo(BaseRepository[JobResult]):
    """job_results 테이블 접근."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=JobResult, session=session, soft_delete_field="")
