"""비밀번호 해싱 및 검증."""

import bcrypt


def hash_password(plain: str) -> str:
    """평문 비밀번호를 bcrypt로 해싱.

    Args:
        plain: 평문 비밀번호.

    Returns:
        bcrypt 해시 문자열.
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """평문 비밀번호와 해시값 비교.

    Args:
        plain: 평문 비밀번호.
        hashed: bcrypt 해시 문자열.

    Returns:
        일치 여부.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
