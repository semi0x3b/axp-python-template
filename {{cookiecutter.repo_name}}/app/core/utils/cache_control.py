"""Cache-Control 응답 헤더 주입용 FastAPI Dependency."""

from __future__ import annotations

from typing import Callable

from fastapi import Response


# 공용 정책 프리셋
HOF_LIST = "public, max-age=300, s-maxage=600, stale-while-revalidate=60"
HOF_DETAIL = "public, max-age=600, s-maxage=3600, stale-while-revalidate=120"


def cache_control(value: str) -> Callable[[Response], None]:
    """지정한 Cache-Control 헤더를 응답에 세팅하는 Dependency를 만든다.

    사용법:
        @router.get("/", dependencies=[Depends(cache_control(cache_control_presets.HOF_LIST))])
    """

    def _dep(response: Response) -> None:
        response.headers["Cache-Control"] = value

    return _dep
