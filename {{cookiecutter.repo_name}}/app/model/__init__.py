"""SQLAlchemy 모델 레지스트리.

Alembic autogenerate가 모든 모델을 인식하려면 이 모듈을 import 해야 한다.

도메인 그룹:
- admin: Admin, AuditLog
- user: User, Role, UserRoleMapping, SmsVerification
- file_upload: FileUpload
- notification: NotificationTemplate
- job: JobResult
"""

from app.model.admin import Admin, AuditLog
from app.model.file_upload import FileUpload
from app.model.job import JobResult
from app.model.notification import NotificationTemplate
from app.model.user import Role, SmsVerification, User, UserRoleMapping

__all__ = [
    "Admin",
    "AuditLog",
    "FileUpload",
    "JobResult",
    "NotificationTemplate",
    "Role",
    "SmsVerification",
    "User",
    "UserRoleMapping",
]
