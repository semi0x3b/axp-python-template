from enum import Enum


class RedisKey(str, Enum):
    """Redis 키 템플릿."""

    POST_VIEW_COUNT = "post:views:{post_id}"
    CHAT_UNREAD_COUNT = "chat:unread:{user_id}"
    MENU_DETAIL = "menu:detail:{menu_public_id}:{cache_key}"
    MENU_TREE = "menu:tree:{cache_key}"
    USER_ME = "user:me:{user_public_id}"
    PASSWORD_RESET = "password_reset:{token}"

    def format(self, **kwargs: object) -> str:
        """키 템플릿에 파라미터를 치환한다."""
        return self.value.format(**kwargs)
