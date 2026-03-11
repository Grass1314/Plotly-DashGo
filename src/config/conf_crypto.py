"""
配置文件敏感值加解密模块。

独立于 util_encrypt.py（后者依赖 CommonConf），避免循环依赖。
使用 AES-256-GCM 带认证加密，主密钥通过环境变量 DASHGO_MASTER_KEY 传入。

加密格式: ENC(base64(nonce_12 + ciphertext + tag_16))
"""

import base64
import hashlib
import os
import re

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

ENV_MASTER_KEY = 'DASHGO_MASTER_KEY'
_ENC_PATTERN = re.compile(r'^ENC\((.+)\)$')

NONCE_SIZE = 12
TAG_SIZE = 16


def _derive_key(master_key: str) -> bytes:
    """SHA-256 派生 32 字节 AES 密钥"""
    return hashlib.sha256(master_key.encode('utf-8')).digest()


def get_master_key() -> str | None:
    return os.environ.get(ENV_MASTER_KEY)


def is_encrypted(value: str) -> bool:
    return bool(_ENC_PATTERN.match(value.strip()))


def encrypt_value(plaintext: str, master_key: str) -> str:
    """加密明文，返回 ENC(base64...) 格式字符串"""
    key = _derive_key(master_key)
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    payload = base64.b64encode(nonce + ciphertext + tag).decode('ascii')
    return f'ENC({payload})'


def decrypt_value(enc_string: str, master_key: str) -> str:
    """解密 ENC(base64...) 格式字符串，返回明文"""
    m = _ENC_PATTERN.match(enc_string.strip())
    if not m:
        raise ValueError(f'Not a valid ENC(...) value: {enc_string!r}')
    raw = base64.b64decode(m.group(1))
    if len(raw) < NONCE_SIZE + TAG_SIZE:
        raise ValueError('Encrypted payload too short')
    nonce = raw[:NONCE_SIZE]
    tag = raw[-TAG_SIZE:]
    ciphertext = raw[NONCE_SIZE:-TAG_SIZE]
    key = _derive_key(master_key)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode('utf-8')
