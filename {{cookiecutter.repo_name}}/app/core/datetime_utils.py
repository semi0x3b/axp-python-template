"""날짜/시간 유틸리티."""

from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def previous_month() -> tuple[int, int]:
    """현재 KST 기준 전월의 (year, month)를 반환한다."""
    now = datetime.now(KST)
    if now.month == 1:
        return now.year - 1, 12
    return now.year, now.month - 1
