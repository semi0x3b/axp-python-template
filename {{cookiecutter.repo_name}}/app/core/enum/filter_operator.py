from enum import Enum


class FilterOperator(str, Enum):
    """필터 연산자 Enum.

    Attributes:
        EQUAL: 단일 컬럼 동등 비교 (=)
        LIKE: 단일 컬럼 LIKE 비교
        IN: 단일 컬럼 IN 비교
        GTE: 단일 컬럼 이상 비교 (>=)
        LTE: 단일 컬럼 이하 비교 (<=)
        OR_LIKE: 다중 컬럼에 대해 OR + LIKE 비교
        OR_EQUAL: 다중 컬럼에 대해 OR + EQUAL 비교
        OR_MULTI: 다중 컬럼 × 다중 값 OR 비교
    """

    EQUAL = "EQUAL"
    LIKE = "LIKE"
    IN = "IN"
    GTE = "GTE"
    LTE = "LTE"
    OR_LIKE = "OR_LIKE"
    OR_EQUAL = "OR_EQUAL"
    OR_MULTI = "OR_MULTI"
