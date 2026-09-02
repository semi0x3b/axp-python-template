from __future__ import annotations

import math
from typing import (
    Any,
    Type,
    TypeVar,
    Generic,
    Optional,
    List,
    Dict,
    Union,
    Sequence,
)

from pydantic import BaseModel
from sqlalchemy import select, update, delete, and_, or_, func, desc, insert, UnaryExpression
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum.filter_operator import FilterOperator
from app.core.enum.response_message import ErrorResponseMessage
from app.core.schema.search_request import SearchFilter
from app.core.exception.handlers import NotFoundError

ModelType = TypeVar("ModelType")
T = TypeVar("T")


class BaseRepository(Generic[ModelType]):
    """기본 Repository 클래스.

    Soft Delete(is_active 필드)를 지원하며, 제네릭 CRUD + 필터링 + 페이지네이션을 제공한다.
    """

    # 암호화(BYTEA) 등 SQL 필터링이 불가능한 컬럼. 하위 클래스에서 오버라이드.
    _UNSEARCHABLE_COLUMNS: set[str] = set()

    def __init__(
        self,
        model: Type[ModelType],
        session: AsyncSession,
        soft_delete_field: str = "is_active",
        deleted_at_field: str | None = None,
    ):
        self.model = model
        self.session = session
        self.soft_delete_field = soft_delete_field
        self.deleted_at_field = deleted_at_field

    # ──────────────────────────────────────────────
    # 내부 유틸
    # ──────────────────────────────────────────────
    def _active_condition(self):
        """Soft Delete 활성 상태 조건식을 반환한다.

        is_active 필드와 deleted_at 필드를 모두 지원한다.
        """
        conditions = []
        if self.soft_delete_field and hasattr(self.model, self.soft_delete_field):
            conditions.append(getattr(self.model, self.soft_delete_field) == True)  # noqa: E712
        if self.deleted_at_field and hasattr(self.model, self.deleted_at_field):
            conditions.append(getattr(self.model, self.deleted_at_field).is_(None))
        if len(conditions) == 1:
            return conditions[0]
        if len(conditions) > 1:
            return and_(*conditions)
        return None

    def _build_order_by(self, sort: Optional[Union[str, List[str]]]) -> List[UnaryExpression]:
        if not sort:
            return []
        tokens: List[str]
        if isinstance(sort, str):
            tokens = [s.strip() for s in sort.split(",") if s.strip()]
        else:
            tokens = [s.strip() for s in sort if s and s.strip()]

        order_bys: List[UnaryExpression] = []
        for token in tokens:
            desc_flag = token.startswith("-")
            name = token.lstrip("-")
            attr = self.model
            ok = True
            for part in name.split("."):
                if hasattr(attr, part):
                    attr = getattr(attr, part)
                else:
                    ok = False
                    break
            if not ok:
                continue
            order_bys.append(desc(attr) if desc_flag else attr.asc())
        return order_bys

    # ──────────────────────────────────────────────
    # 조회
    # ──────────────────────────────────────────────
    async def get_by_id(self, id: Any, *, include_inactive: bool = False) -> Optional[ModelType]:
        """ID로 단일 객체를 조회한다."""
        query = select(self.model).where(self.model.id == id)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, id: Any, *, include_inactive: bool = False) -> ModelType:
        """ID로 조회하고, 없으면 NotFoundError를 발생시킨다."""
        obj = await self.get_by_id(id, include_inactive=include_inactive)
        if not obj:
            raise NotFoundError(detail=ErrorResponseMessage.NO_DATA_FOUND)
        return obj

    async def get_by_public_id(self, public_id: Any, *, include_inactive: bool = False) -> Optional[ModelType]:
        """public_id로 단일 객체를 조회한다."""
        query = select(self.model).where(self.model.public_id == public_id)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_public_id_or_raise(self, public_id: Any, *, include_inactive: bool = False) -> ModelType:
        """public_id로 조회하고, 없으면 NotFoundError를 발생시킨다."""
        obj = await self.get_by_public_id(public_id, include_inactive=include_inactive)
        if not obj:
            raise NotFoundError(detail=ErrorResponseMessage.NO_DATA_FOUND)
        return obj

    async def get_id_by_public_id(self, public_id: Any, *, include_inactive: bool = False) -> int:
        """public_id로 내부 ID(int)를 조회한다. 없으면 NotFoundError.

        API에서 public_id를 받아 FK 조인용 내부 ID가 필요할 때 사용한다.
        """
        query = select(self.model.id).where(self.model.public_id == public_id)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(detail=ErrorResponseMessage.NO_DATA_FOUND)
        return row

    async def get_ids_by_public_ids(self, public_ids: list[Any], *, include_inactive: bool = False) -> Dict[str, int]:
        """public_id 목록을 {str(public_id): id} 맵으로 변환한다.

        batch 조회 시 public_id → id 매핑이 필요할 때 사용한다.
        """
        if not public_ids:
            return {}
        query = select(self.model.public_id, self.model.id).where(self.model.public_id.in_(public_ids))
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query)
        return {str(row[0]): row[1] for row in result.all()}

    async def get_by(self, *, include_inactive: bool = False, **filters) -> Optional[ModelType]:
        """임의의 컬럼 조건으로 단일 객체를 조회한다."""
        query = select(self.model)
        for k, v in filters.items():
            if hasattr(self.model, k):
                query = query.where(getattr(self.model, k) == v)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_by_or_raise(self, *, include_inactive: bool = False, **filters) -> ModelType:
        """임의의 컬럼 조건으로 조회하고, 없으면 NotFoundError를 발생시킨다."""
        result = await self.get_by(include_inactive=include_inactive, **filters)
        if result is None:
            raise NotFoundError(ErrorResponseMessage.NO_DATA_FOUND)
        return result

    async def list(
        self,
        *,
        filters: Optional[Union[Dict[str, Any], SearchFilter]] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[Union[str, List[str]]] = None,
        include_inactive: bool = False,
    ) -> Sequence[ModelType]:
        """목록을 조회한다."""
        query = select(self.model)
        if filters:
            query = self.apply_filters(query, filters)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        if sort:
            order_bys = self._build_order_by(sort)
            if order_bys:
                query = query.order_by(*order_bys)
        if limit:
            query = query.offset(offset).limit(limit)
        elif offset:
            query = query.offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_list_with_pagination(
        self,
        filters: Optional[Union[Dict[str, Any], SearchFilter]] = None,
        offset: int = 0,
        limit: int = 50,
        sort: Any = None,
        include_inactive: bool = False,
    ) -> tuple[Sequence[ModelType], dict]:
        """목록을 조회하고 페이지네이션 정보를 함께 반환한다."""
        data = await self.list(
            filters=filters,
            offset=offset,
            limit=limit,
            sort=sort,
            include_inactive=include_inactive,
        )
        total_count = await self.count(filters=filters, include_inactive=include_inactive)

        total_page = math.ceil(total_count / limit) if limit else 1
        pagination = {
            "total_count": total_count,
            "page": (offset // limit + 1) if limit else 1,
            "limit": limit,
            "count": len(data),
            "total_page": total_page,
        }
        return data, pagination

    # ──────────────────────────────────────────────
    # 생성
    # ──────────────────────────────────────────────
    async def create(self, obj_in: Dict[str, Any], *, actor: str = None) -> ModelType:
        """단일 객체를 생성한다."""
        if actor and isinstance(obj_in, dict):
            obj_in.setdefault("created_by", actor)
            obj_in.setdefault("updated_by", actor)
        if isinstance(obj_in, self.model):
            obj = obj_in
        else:
            obj = self.model(**obj_in)
        return await self.save(obj)

    async def bulk_create(self, obj_list: List[Dict[str, Any]]) -> List[ModelType]:
        """여러 객체를 일괄 생성한다."""
        stmt = insert(self.model).values(obj_list).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ──────────────────────────────────────────────
    # 수정
    # ──────────────────────────────────────────────
    async def update(self, obj: ModelType, obj_in: Union[Dict[str, Any], BaseModel], *, actor: str = None) -> ModelType:
        """기존 객체를 수정한다."""
        if isinstance(obj_in, BaseModel):
            data = obj_in.model_dump(exclude_unset=True)
        else:
            data = dict(obj_in)
        if actor:
            data["updated_by"] = actor
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        await self.session.flush()
        return obj

    async def update_by_id(self, id: Any, obj_in: Union[Dict[str, Any], BaseModel]) -> ModelType:
        """ID 기반으로 부분 업데이트를 수행한다."""
        if isinstance(obj_in, BaseModel):
            values = obj_in.model_dump(exclude_unset=True)
        else:
            values = obj_in
        stmt = update(self.model).where(self.model.id == id).values(**values).returning(self.model)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundError(f"{self.model.__name__}({id}) not found")
        await self.session.flush()
        return obj

    async def save(self, obj: ModelType) -> ModelType:
        """엔티티 변경 내용을 DB에 반영한다."""
        self.session.add(obj)
        await self.session.flush()
        return obj

    # ──────────────────────────────────────────────
    # Soft Delete / Restore
    # ──────────────────────────────────────────────
    async def soft_delete(self, obj: ModelType, updated_by: str = None) -> ModelType:
        """객체를 Soft Delete 처리한다."""
        if not hasattr(obj, self.soft_delete_field):
            raise AttributeError(f"{self.model.__name__} has no field '{self.soft_delete_field}'")
        setattr(obj, self.soft_delete_field, False)
        if updated_by and hasattr(obj, "updated_by"):
            obj.updated_by = updated_by
        await self.session.flush()
        return obj

    async def soft_delete_by_id(self, id: Any, updated_by: str = None) -> ModelType:
        """ID로 객체를 Soft Delete 처리한다."""
        obj = await self.get_by_id_or_raise(id, include_inactive=True)
        return await self.soft_delete(obj, updated_by=updated_by)

    async def restore(self, obj: ModelType) -> ModelType:
        """Soft Delete 된 객체를 복구한다."""
        if not hasattr(obj, self.soft_delete_field):
            raise AttributeError(f"{self.model.__name__} has no field '{self.soft_delete_field}'")
        setattr(obj, self.soft_delete_field, True)
        await self.session.flush()
        return obj

    async def restore_by_id(self, id: Any) -> ModelType:
        """ID로 Soft Delete 된 객체를 복구한다."""
        obj = await self.get_by_id_or_raise(id, include_inactive=True)
        return await self.restore(obj)

    # ──────────────────────────────────────────────
    # 하드 삭제
    # ──────────────────────────────────────────────
    async def delete(self, obj: ModelType) -> None:
        """객체를 하드 삭제한다."""
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_by_id(self, id: Any) -> None:
        """ID로 객체를 하드 삭제한다."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(f"{self.model.__name__}({id}) not found")
        await self.session.flush()

    # ──────────────────────────────────────────────
    # 필터 적용
    # ──────────────────────────────────────────────
    @staticmethod
    def _make_condition(col: Any, condition: Any) -> Any:
        """컬럼과 FilterCondition에 따라 SQLAlchemy 조건식을 생성한다."""
        if condition.operator == FilterOperator.EQUAL:
            return col == condition.value
        elif condition.operator == FilterOperator.LIKE:
            return col.ilike(condition.value)
        elif condition.operator == FilterOperator.IN:
            return col.in_(condition.value)
        elif condition.operator == FilterOperator.GTE:
            return col >= condition.value
        elif condition.operator == FilterOperator.LTE:
            return col <= condition.value
        elif condition.operator == FilterOperator.OR_LIKE:
            return col.ilike(condition.value)
        elif condition.operator == FilterOperator.OR_MULTI:
            return or_(*[col == v for v in condition.value])
        else:
            return col == condition.value

    def _resolve_column(self, name: str) -> Any:
        """컬럼 이름을 실제 모델 속성으로 매핑한다. 하위 클래스에서 오버라이드 가능."""
        if name in self._UNSEARCHABLE_COLUMNS:
            return None
        if hasattr(self.model, name):
            return getattr(self.model, name)
        return None

    def _apply_single_condition(self, query: Any, condition: Any) -> Any:
        """SearchFilter의 개별 조건을 쿼리에 적용한다. 하위 클래스에서 오버라이드 가능."""
        if isinstance(condition.column, list):
            or_conds = []
            for col_name in condition.column:
                col = self._resolve_column(col_name)
                if col is not None:
                    or_conds.append(self._make_condition(col, condition))
            if or_conds:
                query = query.where(or_(*or_conds))
        else:
            col = self._resolve_column(condition.column)
            if col is not None:
                query = query.where(self._make_condition(col, condition))
        return query

    def _apply_join_filters(self, query: Any, filters: Union[Dict[str, Any], SearchFilter]) -> Any:
        """JOIN 쿼리에 필터를 적용한다. _resolve_column으로 크로스 테이블 컬럼을 지원한다."""
        if isinstance(filters, dict):
            for key, value in filters.items():
                col = self._resolve_column(key)
                if col is not None:
                    if isinstance(value, (list, tuple)):
                        query = query.where(col.in_(value))
                    else:
                        query = query.where(col == value)
        else:
            for condition in filters.conditions:
                query = self._apply_single_condition(query, condition)
        return query

    def apply_filters(self, query, filters: Union[Dict[str, Any], SearchFilter]):
        """필터 조건을 쿼리에 적용한다 (self.model 컬럼만)."""
        if isinstance(filters, dict):
            conditions = []
            for key, value in filters.items():
                if key in self._UNSEARCHABLE_COLUMNS:
                    continue
                if hasattr(self.model, key):
                    col = getattr(self.model, key)
                    if isinstance(value, (list, tuple)):
                        conditions.append(col.in_(value))
                    else:
                        conditions.append(col == value)
            if conditions:
                query = query.where(and_(*conditions))
        else:
            for condition in filters.conditions:
                if isinstance(condition.column, list):
                    or_conds = []
                    for col_name in condition.column:
                        if col_name in self._UNSEARCHABLE_COLUMNS:
                            continue
                        if hasattr(self.model, col_name):
                            or_conds.append(self._make_condition(getattr(self.model, col_name), condition))
                    if or_conds:
                        query = query.where(or_(*or_conds))
                else:
                    if condition.column in self._UNSEARCHABLE_COLUMNS:
                        continue
                    if not hasattr(self.model, condition.column):
                        continue
                    col_attr = getattr(self.model, condition.column)
                    query = query.where(self._make_condition(col_attr, condition))
        return query

    # ──────────────────────────────────────────────
    # 카운트 / 존재 여부
    # ──────────────────────────────────────────────
    async def count(
        self,
        filters: Optional[Union[Dict[str, Any], SearchFilter]] = None,
        *,
        include_inactive: bool = False,
    ) -> int:
        """조건에 일치하는 레코드 수를 반환한다."""
        query = select(func.count()).select_from(self.model)
        if filters:
            query = self.apply_filters(query, filters)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def exists(
        self,
        filters: Optional[Union[Dict[str, Any], SearchFilter]] = None,
        *,
        include_inactive: bool = False,
    ) -> bool:
        """조건에 일치하는 레코드가 존재하는지 여부를 반환한다."""
        query = select(1).select_from(self.model)
        if filters:
            query = self.apply_filters(query, filters)
        if not include_inactive:
            cond = self._active_condition()
            if cond is not None:
                query = query.where(cond)
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
