"""Backoffice 전용 Enum."""

from enum import Enum


class ComplaintResolution(str, Enum):
    """신고 처리 결과."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WARNING_ISSUED = "WARNING_ISSUED"
