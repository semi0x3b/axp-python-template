"""AES-256-GCM 암호화 및 해시 유틸리티."""

import hashlib
import hmac as hmac_module
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_key() -> bytes:
    """설정에서 AES-256 키(32바이트)를 로드한다."""
    return bytes.fromhex(settings.ENCRYPTION_KEY)


def encrypt_aes256(plaintext: str) -> bytes:
    """AES-256-GCM으로 평문을 암호화한다.

    Args:
        plaintext: 암호화할 평문.

    Returns:
        nonce(12바이트) + ciphertext 바이트열.
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(_get_key())
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_aes256(data: bytes) -> str:
    """AES-256-GCM으로 암호문을 복호화한다.

    Args:
        data: nonce(12바이트) + ciphertext 바이트열.

    Returns:
        복호화된 평문.
    """
    nonce = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(_get_key())
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def compute_blind_index(plaintext: str) -> str:
    """검색용 blind index를 생성한다 (HMAC-SHA256).

    같은 평문 → 항상 같은 해시. exact match 검색에 사용.
    원본 복원 불가.

    Args:
        plaintext: 해시할 평문.

    Returns:
        HMAC-SHA256 hex 문자열 (64자).
    """
    key = _get_key()
    return hmac_module.new(key, plaintext.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_phone(phone: str) -> str:
    """전화번호를 SHA-256으로 해싱한다.

    Args:
        phone: 전화번호 (하이픈 제거 상태).

    Returns:
        SHA-256 해시 hex 문자열.
    """
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()
