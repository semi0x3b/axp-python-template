"""텍스트 처리 유틸리티."""

import re
from typing import Annotated

from pydantic import BeforeValidator

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html_tags(html: str) -> str:
    """HTML 태그를 제거하고 순수 텍스트만 반환한다."""
    return _HTML_TAG_RE.sub("", html)


def content_preview(content: str | None, max_length: int = 140) -> str:
    """게시글 본문에서 HTML 태그를 제거한 미리보기 텍스트를 반환한다."""
    if not content:
        return ""
    text = strip_html_tags(content).strip()
    return text[:max_length]


ContentPreview = Annotated[str, BeforeValidator(lambda v: content_preview(v))]
"""Pydantic 필드 타입: 값 할당 시 자동으로 HTML 태그 제거 + 140자 truncate."""

ContentPreview100 = Annotated[str, BeforeValidator(lambda v: content_preview(v, max_length=100))]
"""Pydantic 필드 타입: 값 할당 시 자동으로 HTML 태그 제거 + 100자 truncate."""
