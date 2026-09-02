"""Timezone Utils

시간대 관련 유틸리티를 제공합니다.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from contextvars import ContextVar
from zoneinfo import ZoneInfo

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

# 요청 스코프 타임존 컨텍스트 (기본 Asia/Seoul)
_CURRENT_TZ: ContextVar[str] = ContextVar("current_tz", default="Asia/Seoul")


def get_now() -> datetime:
    """현재 시간을 한국 시간으로 반환"""
    return datetime.now(KST)


def to_kst(dt: datetime) -> datetime:
    """임의의 datetime → KST naive datetime"""
    # 1) tz‑naive면 UTC로 간주
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 2) KST로 변환
    return dt.astimezone(KST)


def to_utc(dt: datetime) -> datetime:
    """한국 시간을 UTC로 변환"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt.astimezone(timezone.utc)


def to_timezone(dt: datetime, tz_name: str) -> datetime:
    """임의의 datetime을 지정 타임존의 aware datetime으로 변환합니다.

    - 입력이 naive면 UTC로 간주
    - 변환 실패 시 원본을 반환
    """
    if dt is None:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
        return dt.astimezone(tz)
    except Exception:
        return dt


def process_datetime_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """datetime 문자열을 datetime 객체로 변환"""
    from datetime import datetime

    processed = data.copy()
    for key, value in processed.items():
        if isinstance(value, str) and "T" in value and ("+" in value or "Z" in value):
            try:
                # ISO8601 형식의 문자열을 datetime으로 변환
                if value.endswith("Z"):
                    value = value.replace("Z", "+00:00")
                processed[key] = datetime.fromisoformat(value)
            except ValueError:
                # 변환 실패 시 원본 값 유지
                pass
    return processed


def now_in_timezone(tz_name: str) -> datetime:
    """지정한 타임존의 현재 시간을 반환합니다 (timezone-aware).

    Args:
        tz_name (str): IANA 타임존 문자열 (예: "Asia/Seoul")

    Returns:
        datetime: tz-aware datetime
    """
    try:
        tz = ZoneInfo(tz_name)
        return datetime.now(tz)
    except Exception:
        # fallback: KST
        return datetime.now(KST)


def set_current_timezone(tz_name: str | None) -> None:
    """요청 컨텍스트의 타임존 문자열을 설정한다.

    None 또는 빈 값이 들어오면 기본값(Asia/Seoul) 유지
    """
    if tz_name and isinstance(tz_name, str):
        _CURRENT_TZ.set(tz_name)


def get_current_timezone() -> str:
    """현재 요청 컨텍스트에 설정된 타임존 문자열을 반환한다."""
    return _CURRENT_TZ.get()
