"""감사로그 ASGI 미들웨어.

백오피스 API 요청/응답을 자동으로 감사 로그에 기록한다.
- action 자동 생성 (HTTP 메서드 + URL path → RESOURCE_ACTION 형식)
- 민감 필드 마스킹 (password, token, real_name 등)
- 오류 격리: 감사 로그 기록 실패가 본 요청에 영향 없음
"""

import json
import re
from typing import Any

import jwt
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────

BACKOFFICE_PREFIX = "/api/v1/backoffice/"

SENSITIVE_ENDPOINTS: set[str] = {
    "/api/v1/backoffice/auth/login",
    "/api/v1/backoffice/auth/password",
}

EXCLUDE_ENDPOINTS: set[str] = {
    "/api/v1/backoffice/auth/token/refresh",
}

SENSITIVE_FIELDS: set[str] = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "real_name",
    "real_name_hash",
    "phone",
    "phone_hash",
    "verification_code",
    "conversation_key",
    "message_content",
}

_UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_NUMBER_PATTERN = re.compile(r"^\d+$")

# 복수형 → 단수형 매핑
_PLURAL_TO_SINGULAR: dict[str, str] = {
    "users": "user",
    "posts": "post",
    "menus": "menu",
    "universities": "university",
    "organizations": "organization",
    "members": "member",
    "admins": "admin",
    "comments": "comment",
    "notifications": "notification",
    "complaints": "complaint",
    "reports": "report",
    "announcements": "announcement",
    "badges": "badge",
    "roles": "role",
    "permissions": "permission",
    "logs": "log",
    "files": "file",
    "images": "image",
    "categories": "category",
    "tags": "tag",
    "groups": "group",
    "chats": "chat",
    "messages": "message",
    "competitions": "competition",
    "tasks": "task",
    "events": "event",
    "votes": "vote",
    "rankings": "ranking",
    "settings": "setting",
    "configs": "config",
    "versions": "version",
    "sessions": "session",
    "tokens": "token",
    "profiles": "profile",
    "accounts": "account",
}

# HTTP 메서드 → action suffix 매핑
_METHOD_TO_ACTION: dict[str, str] = {
    "GET_COLLECTION": "LIST",
    "GET_ITEM": "DETAIL",
    "POST": "CREATE",
    "PUT": "UPDATE",
    "PATCH": "UPDATE",
    "DELETE": "DELETE",
}


# ──────────────────────────────────────────────
# 순수 함수
# ──────────────────────────────────────────────


def extract_route_group(path: str) -> str:
    """URL path에서 라우터 그룹(첫 번째 리소스 세그먼트)을 추출한다.

    Args:
        path: URL path (예: `/api/v1/backoffice/users/abc`)

    Returns:
        라우터 그룹 문자열 (예: `"users"`)

    Examples:
        >>> extract_route_group("/api/v1/backoffice/users/abc")
        'users'
        >>> extract_route_group("/api/v1/backoffice/audit-logs/")
        'audit-logs'
    """
    # BACKOFFICE_PREFIX 이후 첫 번째 세그먼트 추출
    if path.startswith(BACKOFFICE_PREFIX):
        remainder = path[len(BACKOFFICE_PREFIX) :]
    else:
        remainder = path.lstrip("/")

    segments = [s for s in remainder.split("/") if s]
    if not segments:
        return ""

    return segments[0]


def _is_identifier(segment: str) -> bool:
    """세그먼트가 UUID 또는 숫자 ID인지 확인한다."""
    return bool(_UUID_PATTERN.match(segment)) or bool(_NUMBER_PATTERN.match(segment))


def _to_upper_snake_case(kebab: str) -> str:
    """kebab-case 또는 일반 문자열을 UPPER_SNAKE_CASE로 변환한다.

    Args:
        kebab: 변환할 문자열 (예: `"audit-logs"`)

    Returns:
        UPPER_SNAKE_CASE 문자열 (예: `"AUDIT_LOGS"`)
    """
    return kebab.replace("-", "_").upper()


def _singularize(word: str) -> str:
    """복수형 단어를 단수형으로 변환한다.

    kebab-case 단어의 경우 마지막 세그먼트만 단수형으로 변환한다.
    예: ``"audit-logs"`` → ``"audit-log"``

    Args:
        word: 복수형 단어 (kebab-case 포함)

    Returns:
        단수형 단어 (매핑 없으면 원본 반환)
    """
    # 직접 매핑 확인
    if word in _PLURAL_TO_SINGULAR:
        return _PLURAL_TO_SINGULAR[word]

    # kebab-case: 마지막 세그먼트만 단수형 변환
    if "-" in word:
        parts = word.split("-")
        last = parts[-1]
        singular_last = _PLURAL_TO_SINGULAR.get(last, last)
        return "-".join(parts[:-1] + [singular_last])

    return word


def generate_action(method: str, path: str) -> str:
    """HTTP 메서드와 URL path로부터 감사 로그 action을 생성한다.

    Rules:
    - URL에서 라우터 그룹(첫 번째 리소스 세그먼트)을 추출해 단수형 UPPER_SNAKE_CASE로 변환
    - 마지막 path 세그먼트가 UUID/숫자가 아니면 suffix로 사용 (예: `suspend` → `_SUSPEND`)
    - UUID/숫자이거나 없으면 HTTP 메서드로 suffix 결정
      - GET + 컬렉션 (마지막이 리소스 그룹 또는 `/`) → LIST
      - GET + 아이템 (마지막이 UUID/숫자) → DETAIL
      - POST → CREATE
      - PUT/PATCH → UPDATE
      - DELETE → DELETE

    Args:
        method: HTTP 메서드 (예: `"GET"`, `"POST"`)
        path: URL path (예: `"/api/v1/backoffice/users/550e8400-e29b-41d4-a716-446655440000"`)

    Returns:
        action 문자열 (예: `"USER_DETAIL"`)

    Examples:
        >>> generate_action("GET", "/api/v1/backoffice/users/")
        'USER_LIST'
        >>> generate_action("POST", "/api/v1/backoffice/users/550e8400-e29b-41d4-a716-446655440000/suspend")
        'USER_SUSPEND'
        >>> generate_action("GET", "/api/v1/backoffice/audit-logs/")
        'AUDIT_LOG_LIST'
    """
    method = method.upper()

    # BACKOFFICE_PREFIX 이후 세그먼트 분리
    if path.startswith(BACKOFFICE_PREFIX):
        remainder = path[len(BACKOFFICE_PREFIX) :]
    else:
        remainder = path.lstrip("/")

    segments = [s for s in remainder.split("/") if s]

    if not segments:
        return f"UNKNOWN_{method}"

    # 라우터 그룹 (첫 번째 세그먼트)
    route_group = segments[0]

    # 단수형으로 변환 후 UPPER_SNAKE_CASE
    singular = _singularize(route_group)
    resource_prefix = _to_upper_snake_case(singular)

    # 마지막 세그먼트 분석
    last_segment = segments[-1]

    # 마지막 세그먼트가 UUID/숫자가 아니고 첫 번째 세그먼트(라우터 그룹)와 다르면 suffix
    if not _is_identifier(last_segment) and last_segment != route_group:
        suffix = _to_upper_snake_case(last_segment)
        return f"{resource_prefix}_{suffix}"

    # HTTP 메서드 기반 suffix
    if method == "GET":
        # 마지막 세그먼트가 UUID/숫자이면 DETAIL, 아니면 LIST
        if _is_identifier(last_segment):
            action_suffix = "DETAIL"
        else:
            action_suffix = "LIST"
    else:
        action_suffix = _METHOD_TO_ACTION.get(method, method)

    return f"{resource_prefix}_{action_suffix}"


def is_sensitive_endpoint(path: str) -> bool:
    """path가 민감 엔드포인트인지 확인한다.

    Args:
        path: URL path

    Returns:
        민감 엔드포인트 여부
    """
    return path in SENSITIVE_ENDPOINTS


def mask_sensitive_data(data: Any) -> Any:
    """민감 필드를 `"***"`로 재귀적으로 마스킹한다.

    Args:
        data: 마스킹할 데이터 (dict, list, 기타)

    Returns:
        민감 필드가 마스킹된 데이터 (원본 불변, 새 객체 반환)
    """
    if data is None:
        return None

    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in SENSITIVE_FIELDS:
                result[key] = "***"
            else:
                result[key] = mask_sensitive_data(value)
        return result

    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]

    return data


# ──────────────────────────────────────────────
# ASGI 미들웨어
# ──────────────────────────────────────────────


class AuditMiddleware:
    """백오피스 API 감사 로그 ASGI 미들웨어.

    `/api/v1/backoffice/` 하위 모든 요청을 감사 로그에 기록한다.
    감사 로그 기록 실패 시 오류를 격리하여 본 요청에 영향을 주지 않는다.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI 진입점."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        if not path.startswith(BACKOFFICE_PREFIX) or path in EXCLUDE_ENDPOINTS:
            await self.app(scope, receive, send)
            return

        # 요청 body 캡처
        request_body_chunks: list[bytes] = []

        async def receive_wrapper() -> dict:
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                if chunk:
                    request_body_chunks.append(chunk)
            return message

        # 응답 status + body 캡처
        response_status: list[int] = []
        response_body_chunks: list[bytes] = []

        async def send_wrapper(message: dict) -> None:
            if message.get("type") == "http.response.start":
                response_status.append(message.get("status", 0))
            elif message.get("type") == "http.response.body":
                chunk = message.get("body", b"")
                if chunk:
                    response_body_chunks.append(chunk)
            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)

        # 감사 로그 기록 (오류 격리)
        try:
            await self._record_audit_log(
                scope=scope,
                request_body_chunks=request_body_chunks,
                response_status=response_status[0] if response_status else 0,
                response_body_chunks=response_body_chunks,
            )
        except Exception as exc:
            logger.error("audit_log_record_failed", error=str(exc), path=path, exc_info=True)

    async def _record_audit_log(
        self,
        scope: Scope,
        request_body_chunks: list[bytes],
        response_status: int,
        response_body_chunks: list[bytes],
    ) -> None:
        """감사 로그를 DB에 기록한다.

        Args:
            scope: ASGI scope
            request_body_chunks: 요청 body 청크 목록
            response_status: HTTP 응답 상태 코드
            response_body_chunks: 응답 body 청크 목록
        """
        from sqlalchemy import select

        from app.db.connection import async_session_factory
        from app.model.admin import Admin, AuditLog

        path: str = scope.get("path", "")
        method: str = scope.get("method", "GET").upper()
        headers: dict[str, str] = {k.decode(): v.decode() for k, v in scope.get("headers", [])}

        # IP 추출 (우선순위: X-Forwarded-For > X-Real-IP > TCP 연결 IP)
        client = scope.get("client")
        ip_address: str | None = client[0] if client else None

        if real_ip := headers.get("x-real-ip"):
            ip_address = real_ip.strip()

        forwarded_for = headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        # JWT에서 admin 정보 추출
        actor_id: int | None = None
        actor_email: str | None = None

        auth_header = headers.get("authorization", "")
        admin_public_id: str | None = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                if payload.get("type") in ("admin_access", "admin_refresh"):
                    admin_public_id = payload.get("sub", "") or None
            except Exception:
                pass  # 인증 실패 시 actor 없이 기록

        # action + route_group 생성
        action = generate_action(method, path)
        route_group = extract_route_group(path)

        # 요청 body 파싱 + 마스킹
        request_body_json: dict | None = None
        if request_body_chunks and not is_sensitive_endpoint(path):
            raw_request = b"".join(request_body_chunks)
            try:
                parsed = json.loads(raw_request.decode("utf-8"))
                request_body_json = mask_sensitive_data(parsed)
            except Exception:
                pass
        elif request_body_chunks and is_sensitive_endpoint(path):
            request_body_json = None  # 민감 엔드포인트는 body 미기록

        # 응답 body 파싱
        response_body_json: dict | None = None
        if response_body_chunks:
            raw_response = b"".join(response_body_chunks)
            try:
                parsed_response = json.loads(raw_response.decode("utf-8"))
                response_body_json = mask_sensitive_data(parsed_response)
            except Exception:
                pass

        # admin 조회 + 감사 로그 저장 (단일 세션)
        async with async_session_factory() as session:
            if admin_public_id:
                try:
                    result = await session.execute(select(Admin.id, Admin.email).where(Admin.public_id == admin_public_id))
                    row = result.first()
                    if row:
                        actor_id = row[0]
                        actor_email = row[1]
                except Exception:
                    pass

            audit_log = AuditLog(
                actor_id=actor_id,
                actor_email=actor_email,
                action=action,
                http_method=method,
                endpoint=path,
                route_group=route_group,
                request_body=request_body_json,
                response_body=response_body_json,
                response_status=response_status,
                ip_address=ip_address,
            )
            session.add(audit_log)
            await session.commit()
