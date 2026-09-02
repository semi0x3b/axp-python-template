"""알림 템플릿 모델."""

from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseIdModel, PublicIdMixin


class NotificationTemplate(BaseIdModel, PublicIdMixin):
    """알림 메시지 템플릿.

    시드 데이터로 등록되며, backoffice에서 content_template과 is_enabled만 수정 가능.
    event_code, title, available_vars는 코드/시드에서 고정.
    """

    __tablename__ = "comn_notification_templates"

    event_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="이벤트 식별자")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="관리용 이름")
    content_template: Mapped[str] = mapped_column(Text, nullable=False, comment="메시지 템플릿 ({var} 치환)")
    available_vars: Mapped[str] = mapped_column(String(200), nullable=False, server_default=text("''"), comment="치환 가능 변수 목록 (콤마 구분)")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), comment="알림 활성 여부")
