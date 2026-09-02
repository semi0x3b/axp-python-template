from datetime import datetime
from typing import Any, List, Optional, Union
from urllib.parse import unquote

from pydantic import BaseModel, Field, field_validator

from app.core.enum.filter_operator import FilterOperator


class FilterCondition(BaseModel):
    """필터 조건

    지원 패턴:
    1. 단일 컬럼 + 단일 값 (EQUAL): filters=status:active
    2. 단일 컬럼 + 단일 값 (LIKE): filters=name:`test`
    3. 단일 컬럼 + 다중 값 (IN): filters=category:backend,devops
    4. 단일 컬럼 + 범위 비교 (GTE/LTE): filters=created_at:gte:2026-03-01
    5. 다중 컬럼 + 단일 값 (OR EQUAL): filters=name,email:semi
    6. 다중 컬럼 + 단일 값 (OR LIKE): filters=name,email:`semi`
    7. 다중 컬럼 + 다중 값 (OR MULTI): filters=name,email:john,jane
    """

    column: Union[str, List[str]] = Field(..., description="검색할 컬럼명 (단일 또는 다중)")
    operator: FilterOperator = Field(..., description="검색 연산자")
    value: Union[str, int, float, bool, datetime, List[Union[str, int, float]]] = Field(..., description="검색 값")

    @field_validator("value")
    @classmethod
    def validate_value_for_operator(cls, v, info):
        operator = info.data.get("operator")
        if operator in [FilterOperator.IN, FilterOperator.OR_MULTI] and not isinstance(v, list):
            raise ValueError(f"{operator.value} 연산자는 리스트 값이 필요합니다")
        if operator in [
            FilterOperator.EQUAL,
            FilterOperator.LIKE,
            FilterOperator.GTE,
            FilterOperator.LTE,
            FilterOperator.OR_LIKE,
            FilterOperator.OR_EQUAL,
        ] and isinstance(v, list):
            raise ValueError(f"{operator.value} 연산자는 단일 값이 필요합니다")
        return v

    @field_validator("column")
    @classmethod
    def validate_column_for_operator(cls, v, info):
        operator = info.data.get("operator")
        if operator in [FilterOperator.OR_LIKE, FilterOperator.OR_EQUAL, FilterOperator.OR_MULTI] and isinstance(v, str):
            raise ValueError(f"{operator.value} 연산자는 여러 컬럼이 필요합니다")
        if operator in [FilterOperator.EQUAL, FilterOperator.LIKE, FilterOperator.IN, FilterOperator.GTE, FilterOperator.LTE] and isinstance(v, list):
            raise ValueError(f"{operator.value} 연산자는 단일 컬럼이 필요합니다")
        return v


# 불리언 파싱 유틸
TRUE_SET = {"true", "1", "t", "y", "yes", "on"}
FALSE_SET = {"false", "0", "f", "n", "no", "off"}


def _looks_boolean_key(columns: List[str]) -> bool:
    return all(c.startswith("is_") for c in columns)


def _coerce_numeric(raw: str) -> Union[int, float, str]:
    """숫자형 문자열을 int/float로 변환한다. 변환 불가 시 원본 문자열 반환."""
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _coerce_bool_for_key(key: str, raw: str) -> bool:
    v = raw.strip().lower()
    if v in TRUE_SET:
        return True
    if v in FALSE_SET:
        return False
    raise ValueError(f"불리언으로 해석할 수 없는 값: {raw!r} (키: {key})")


class SearchFilter(BaseModel):
    conditions: List[FilterCondition] = Field(default_factory=list)

    def add_condition(self, column: Union[str, List[str]], operator: FilterOperator, value: Any) -> None:
        self.conditions.append(FilterCondition(column=column, operator=operator, value=value))

    def to_dict(self) -> List[dict]:
        return [c.model_dump() for c in self.conditions]

    @classmethod
    def from_query_string(cls, filters_str: Optional[str]) -> Optional["SearchFilter"]:
        if not filters_str:
            return None

        sf = cls()
        try:
            for pair in filters_str.split("|"):
                if ":" not in pair:
                    continue

                col_part, value_str = pair.split(":", 1)
                columns = [c.strip() for c in col_part.strip().split(",")]
                raw_values = [v.strip() for v in unquote(value_str.strip()).split(",")]

                values = [v.replace("`", "%") if "`" in v else v for v in raw_values]
                is_bool = _looks_boolean_key(columns)

                if is_bool and any("%" in v for v in values):
                    raise ValueError(f"{columns} 는 불리언 컬럼이므로 LIKE 패턴을 사용할 수 없습니다")

                if len(columns) > 1 and len(values) > 1:
                    sf.add_condition(
                        columns,
                        FilterOperator.OR_MULTI,
                        [_coerce_bool_for_key(columns[0], v) for v in values] if is_bool else [_coerce_numeric(v) for v in values],
                    )
                elif len(columns) > 1 and len(values) == 1:
                    v = values[0]
                    if "%" in v:
                        sf.add_condition(columns, FilterOperator.OR_LIKE, v)
                    else:
                        sf.add_condition(
                            columns,
                            FilterOperator.OR_EQUAL,
                            _coerce_bool_for_key(columns[0], v) if is_bool else _coerce_numeric(v),
                        )
                elif len(columns) == 1 and len(values) > 1:
                    col = columns[0]
                    sf.add_condition(
                        col,
                        FilterOperator.IN,
                        [_coerce_bool_for_key(col, v) for v in values] if is_bool else [_coerce_numeric(v) for v in values],
                    )
                else:
                    col, v = columns[0], values[0]
                    if v.startswith("gte:"):
                        sf.add_condition(col, FilterOperator.GTE, _coerce_numeric(v[4:]))
                    elif v.startswith("lte:"):
                        sf.add_condition(col, FilterOperator.LTE, _coerce_numeric(v[4:]))
                    elif "%" in v:
                        sf.add_condition(col, FilterOperator.LIKE, v)
                    else:
                        sf.add_condition(
                            col,
                            FilterOperator.EQUAL,
                            _coerce_bool_for_key(col, v) if is_bool else _coerce_numeric(v),
                        )

        except Exception as e:
            raise ValueError(f"필터 파싱 오류: {str(e)}")

        return sf if sf.conditions else None
