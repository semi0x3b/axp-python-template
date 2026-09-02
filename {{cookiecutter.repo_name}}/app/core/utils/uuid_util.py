import uuid


class UUIDUtil:
    """UUID 생성 유틸리티 클래스"""

    @staticmethod
    def generate(as_str: bool = True, remove_hyphen: bool = False, prefix: str | None = None):
        """UUID를 생성합니다.

        Args:
            as_str (bool, optional): UUID를 문자열로 반환할지 여부. 기본값 True.
            remove_hyphen (bool, optional): UUID 문자열의 하이픈(-) 제거 여부. 기본값 False.
            prefix (str | None, optional): 접두사(prefix)를 추가할 경우 설정.

        Returns:
            Union[str, uuid.UUID]: 생성된 UUID 값. as_str=True면 문자열, 아니면 uuid.UUID 객체.
        """
        uid = uuid.uuid4()

        if as_str:
            uid_str = str(uid)
            if remove_hyphen:
                uid_str = uid_str.replace("-", "")
            if prefix:
                uid_str = f"{prefix}{uid_str}"
            return uid_str

        return uid
