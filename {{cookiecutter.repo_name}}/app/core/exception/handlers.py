from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError

from app.core.enum.response_message import ErrorResponseMessage
from app.core.logger import get_logger
from app.core.schema.response import ErrorResponse, ErrorDetail

logger = get_logger(__name__)


# ──────────────────────────────────────────────
# Custom HTTP Exceptions
# ──────────────────────────────────────────────
class BadRequestError(HTTPException):
    """400 Bad Request"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedError(HTTPException):
    """401 Unauthorized"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(HTTPException):
    """403 Forbidden"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    """404 Not Found"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """409 Conflict"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(HTTPException):
    """422 Unprocessable Entity"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class RateLimitError(HTTPException):
    """429 Too Many Requests"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


class BusinessLogicError(HTTPException):
    """비즈니스 로직 처리 실패"""

    def __init__(self, detail: dict):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────
def _build_error_detail(detail) -> ErrorDetail:
    """exc.detail이 dict이면 unpack, str이면 UNKNOWN_ERROR 코드로 감싼다."""
    if isinstance(detail, dict):
        return ErrorDetail(**detail)
    return ErrorDetail(
        code=ErrorResponseMessage.UNKNOWN_ERROR["code"],
        message=str(detail),
    )


# ──────────────────────────────────────────────
# Exception Handler 등록
# ──────────────────────────────────────────────
def setup_exception_handlers(app: FastAPI) -> None:
    """FastAPI 애플리케이션에 공통 예외 처리기를 등록한다."""

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: Request, exc: BadRequestError):
        logger.error(f"BadRequestError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="입력 정보를 다시 확인해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        logger.error(f"UnauthorizedError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="로그인이 만료되었습니다. 다시 로그인해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        logger.error(f"ForbiddenError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="접근 권한이 없습니다.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        logger.error(f"NotFoundError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="요청하신 정보를 찾을 수 없습니다.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        logger.error(f"ConflictError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.error(f"ValidationError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="입력 정보를 다시 확인해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_body.model_dump())

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        logger.warning(f"RateLimitError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(BusinessLogicError)
    async def business_logic_handler(request: Request, exc: BusinessLogicError):
        logger.error(f"BusinessLogicError: {exc.detail} - {request.url}")
        error_detail = _build_error_detail(exc.detail)
        error_body = ErrorResponse(
            success=False,
            message="입력 정보를 다시 확인해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(request: Request, exc: PydanticValidationError):
        logger.error(f"PydanticValidationError: {exc.errors()} - {request.url}")
        errors = [{"field": " -> ".join(str(loc) for loc in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        error_body = ErrorResponse(
            success=False,
            message="입력 정보를 다시 확인해주세요.",
            error=ErrorDetail(
                code=ErrorResponseMessage.PYDANTIC_VALIDATION_ERROR["code"],
                message=ErrorResponseMessage.PYDANTIC_VALIDATION_ERROR["message"],
                data=errors,
            ),
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        logger.error(f"RequestValidationError: {exc.errors()} - {request.url}")
        errors = [{"field": " -> ".join(str(loc) for loc in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        error_body = ErrorResponse(
            success=False,
            message="입력 정보를 다시 확인해주세요.",
            error=ErrorDetail(
                code=ErrorResponseMessage.REQUEST_VALIDATION_ERROR["code"],
                message=ErrorResponseMessage.REQUEST_VALIDATION_ERROR["message"],
                data=errors,
            ),
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_body.model_dump())

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database Error: {exc} - {request.url}", exc_info=True)
        error_detail = ErrorDetail(**ErrorResponseMessage.DATABASE_ERROR)
        error_body = ErrorResponse(
            success=False,
            message="일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_body.model_dump())

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {exc} - {request.url}", exc_info=True)
        error_detail = ErrorDetail(**ErrorResponseMessage.UNKNOWN_ERROR)
        if exc:
            error_detail.message = str(exc)
        error_body = ErrorResponse(
            success=False,
            message="일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            error=error_detail,
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_body.model_dump())
