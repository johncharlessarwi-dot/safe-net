"""Encryption for secrets stored in the database (tenants' ClickPesa keys).

Uses DATA_ENCRYPTION_KEY (a Fernet key) when set, otherwise a key derived from
SECRET_KEY. Changing the key makes stored secrets unreadable: tenants would
have to enter their payment keys again.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config import Config


def _fernet():
    key = Config.DATA_ENCRYPTION_KEY
    if not key:
        key = base64.urlsafe_b64encode(hashlib.sha256(f'safenet-data:{Config.SECRET_KEY}'.encode()).digest())
    return Fernet(key)


def encrypt(value):
    return _fernet().encrypt(value.encode()).decode() if value else None


def decrypt(token):
    if not token:
        return ''
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return ''
