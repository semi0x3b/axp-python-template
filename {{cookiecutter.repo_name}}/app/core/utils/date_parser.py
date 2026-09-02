"""날짜 파싱 및 시간 키워드 감지 유틸리티"""

from datetime import date, datetime, timedelta
from typing import Optional, Union
import re


def get_weekday(d: Union[date, datetime]) -> str:
    """날짜에서 요일 문자열 반환.

    Args:
        d: 날짜 (date 또는 datetime)

    Returns:
        요일 문자열 (월, 화, 수, 목, 금, 토, 일)
    """
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return weekdays[d.weekday()]


def detect_temporal_keywords(query: str) -> Optional[str]:
    """시간 관련 키워드 감지하여 타입 반환

    Args:
        query: 사용자 질문

    Returns:
        - "today": 오늘
        - "tomorrow": 내일
        - "day_after_tomorrow": 모레
        - "yesterday": 어제
        - "two_days_ago": 그제/그저께/엊그제
        - "three_days_after": 글피
        - "three_days_ago": 그끄저께
        - "this_week": 이번 주
        - "next_week": 다음 주
        - "specific_date": 특정 날짜 (YYYY-MM-DD)
        - None: 시간 키워드 없음
    """
    query_lower = query.lower()

    # 특정 날짜 패턴 (YYYY-MM-DD) - 가장 우선
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    if re.search(date_pattern, query):
        return "specific_date"

    # 오늘 키워드
    today_keywords = ["오늘", "today", "오늘의", "오늘은"]
    if any(k in query_lower for k in today_keywords):
        return "today"

    # 내일 키워드
    tomorrow_keywords = ["내일", "tomorrow", "내일의", "내일은"]
    if any(k in query_lower for k in tomorrow_keywords):
        return "tomorrow"

    # 모레 키워드
    day_after_tomorrow_keywords = ["모레", "day after tomorrow"]
    if any(k in query_lower for k in day_after_tomorrow_keywords):
        return "day_after_tomorrow"

    # 어제 키워드
    yesterday_keywords = ["어제", "yesterday", "어제의", "어제는"]
    if any(k in query_lower for k in yesterday_keywords):
        return "yesterday"

    # 그제/그저께/엊그제 (2일 전)
    two_days_ago_keywords = ["그제", "그저께", "엊그제"]
    if any(k in query_lower for k in two_days_ago_keywords):
        return "two_days_ago"

    # 글피 (3일 후)
    three_days_after_keywords = ["글피"]
    if any(k in query_lower for k in three_days_after_keywords):
        return "three_days_after"

    # 그끄저께 (3일 전)
    three_days_ago_keywords = ["그끄저께"]
    if any(k in query_lower for k in three_days_ago_keywords):
        return "three_days_ago"

    # 이번 주 키워드
    this_week_keywords = ["이번주", "이번 주", "this week"]
    if any(k in query_lower for k in this_week_keywords):
        return "this_week"

    # 다음 주 키워드
    next_week_keywords = ["다음주", "다음 주", "next week"]
    if any(k in query_lower for k in next_week_keywords):
        return "next_week"

    return None


def parse_target_date(query: str, current_date: Optional[datetime] = None) -> Optional[str]:
    """시간 키워드를 YYYY-MM-DD 형식으로 변환

    Args:
        query: 사용자 질문
        current_date: 기준 날짜 (기본값: 현재 시각)

    Returns:
        YYYY-MM-DD 형식의 날짜 문자열, 또는 None
    """
    if current_date is None:
        from app.core.utils.timezone import get_now

        current_date = get_now()

    normalized = (query or "").strip()
    if not normalized:
        return None

    # 0) 한국어 날짜 표현 (예: 2025년 12월 23일 / 12월 23일)
    # - 커리큘럼 질문에서 가장 흔한 표현이므로 우선 처리
    m = re.search(r"(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", normalized)
    if m:
        try:
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass

    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", normalized)
    if m:
        try:
            month = int(m.group(1))
            day = int(m.group(2))
            year = int(current_date.strftime("%Y"))
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass

    # 1) 숫자 구분자 형태 (예: 2025/12/23, 2025.12.23, 12/23, 12.23)
    m = re.search(r"(20\d{2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{1,2})", normalized)
    if m:
        try:
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass

    m = re.search(r"(\d{1,2})\s*[./]\s*(\d{1,2})", normalized)
    if m:
        try:
            month = int(m.group(1))
            day = int(m.group(2))
            year = int(current_date.strftime("%Y"))
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass

    temporal_type = detect_temporal_keywords(query)

    if temporal_type == "today":
        return current_date.strftime("%Y-%m-%d")

    elif temporal_type == "tomorrow":
        return (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

    elif temporal_type == "day_after_tomorrow":
        return (current_date + timedelta(days=2)).strftime("%Y-%m-%d")

    elif temporal_type == "yesterday":
        return (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

    elif temporal_type == "two_days_ago":
        return (current_date - timedelta(days=2)).strftime("%Y-%m-%d")

    elif temporal_type == "three_days_after":
        return (current_date + timedelta(days=3)).strftime("%Y-%m-%d")

    elif temporal_type == "three_days_ago":
        return (current_date - timedelta(days=3)).strftime("%Y-%m-%d")

    elif temporal_type == "this_week":
        # 이번 주 월요일 반환 (주의 시작)
        weekday = current_date.weekday()  # 0=월요일
        monday = current_date - timedelta(days=weekday)
        return monday.strftime("%Y-%m-%d")

    elif temporal_type == "next_week":
        # 다음 주 월요일
        weekday = current_date.weekday()
        next_monday = current_date + timedelta(days=(7 - weekday))
        return next_monday.strftime("%Y-%m-%d")

    elif temporal_type == "specific_date":
        # 쿼리에서 YYYY-MM-DD 추출
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern, query)
        if match:
            return match.group(1)

    return None
