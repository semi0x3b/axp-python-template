"""EventBridge 기반 Job Runner.

EventBridge가 job name을 전달하면, JOB_REGISTRY에서 func_path를 찾아 실행한다.
실행 결과는 job_results 테이블에 기록한다.

func_path 포맷:
- UseCase 메서드: "app.domain.job.user.usecase.badge_usecase:BadgeUseCase.expire_outdated_badges"
- 일반 함수:     "app.domain.job.tasks:run_ping"
"""

import importlib
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.logger import get_logger
from app.db.connection import async_session_factory
from app.domain.job.scheduler.repo.result_repo import ResultRepo

logger = get_logger(__name__)

KST = ZoneInfo("Asia/Seoul")

# Job 이름 → func_path 매핑
JOB_REGISTRY: dict[str, dict] = {
    "ping": {
        "func": "app.domain.job.tasks:run_ping",
    },
}


def _resolve_callable(func_path: str) -> tuple[str, str, str | None]:
    """func 경로를 파싱하여 (module_path, class_or_func, method_name) 을 반환한다.

    포맷:
        "module.path:ClassName.method_name" → ("module.path", "ClassName", "method_name")
        "module.path:function_name"         → ("module.path", "function_name", None)

    Raises:
        ValueError: 포맷이 올바르지 않을 때.
    """
    if ":" not in func_path:
        raise ValueError(f"func 포맷 오류: ':' 구분자 필요 (입력: {func_path})")

    module_path, callable_path = func_path.split(":", 1)

    if "." in callable_path:
        class_name, method_name = callable_path.split(".", 1)
        return module_path, class_name, method_name
    else:
        return module_path, callable_path, None


async def execute(job_name: str, params: dict | None = None) -> None:
    """job name으로 등록된 태스크를 실행하고 결과를 기록한다.

    Args:
        job_name: JOB_REGISTRY에 등록된 job 이름.
        params: EventBridge event에서 전달된 파라미터. registry 기본값을 오버라이드.
    """
    logger.info("runner_started", job=job_name)

    job_config = JOB_REGISTRY.get(job_name)
    if not job_config:
        logger.error("runner_unknown_job", job=job_name)
        raise ValueError(f"Unknown job: {job_name}")

    func_path = job_config["func"]
    params = params or job_config.get("params")

    await _execute_task(job_name, func_path, params)

    logger.info("runner_finished", job=job_name)


async def _execute_task(job_name: str, func_path: str, params: dict | None) -> None:
    """단일 태스크를 실행하고 결과를 기록한다."""
    # func_path 파싱
    try:
        module_path, class_or_func, method_name = _resolve_callable(func_path)
    except ValueError as e:
        logger.error("task_resolve_failed", func=func_path, error=str(e))
        await _record_failure(job_name, func_path, params, str(e))
        return

    # 모듈 import
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        logger.error("task_import_failed", func=func_path, error=str(e))
        await _record_failure(job_name, func_path, params, f"ImportError: {e}")
        return

    # STARTED 기록
    started_at = datetime.now(KST)
    async with async_session_factory() as session:
        result_repo = ResultRepo(session)
        job_result = await result_repo.create(
            {
                "job_name": job_name,
                "func": func_path,
                "params": params,
                "status": "STARTED",
                "started_at": started_at,
            }
        )
        await session.commit()
        result_id = job_result.id

    # 태스크 실행
    try:
        kwargs = params or {}

        if method_name:
            async with async_session_factory() as task_session:
                try:
                    cls = getattr(module, class_or_func)
                    instance = cls(task_session)
                    method = getattr(instance, method_name)
                    task_result = await method(**kwargs)
                    await task_session.commit()
                except Exception:
                    await task_session.rollback()
                    raise
        else:
            func = getattr(module, class_or_func)
            task_result = await func(**kwargs)

        # SUCCESS 기록
        async with async_session_factory() as session:
            result_repo = ResultRepo(session)
            job_result = await result_repo.get_by_id(result_id)
            if job_result:
                result_data = task_result if isinstance(task_result, dict) else None
                await result_repo.update(
                    job_result,
                    {
                        "status": "SUCCESS",
                        "result": result_data,
                        "ended_at": datetime.now(KST),
                    },
                )
            await session.commit()

        logger.info("task_succeeded", job=job_name, func=func_path)

    except Exception as e:
        # FAILED 기록
        async with async_session_factory() as session:
            result_repo = ResultRepo(session)
            job_result = await result_repo.get_by_id(result_id)
            if job_result:
                await result_repo.update(
                    job_result,
                    {
                        "status": "FAILED",
                        "error": f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                        "ended_at": datetime.now(KST),
                    },
                )
            await session.commit()

        logger.error("task_failed", job=job_name, func=func_path, error=str(e))


async def _record_failure(job_name: str, func_path: str, params: dict | None, error: str) -> None:
    """import/resolve 실패 시 결과를 기록한다."""
    async with async_session_factory() as session:
        result_repo = ResultRepo(session)
        now = datetime.now(KST)
        await result_repo.create(
            {
                "job_name": job_name,
                "func": func_path,
                "params": params,
                "status": "FAILED",
                "error": error,
                "started_at": now,
                "ended_at": now,
            }
        )
        await session.commit()
