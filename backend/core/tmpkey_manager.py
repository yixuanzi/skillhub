"""TmpKey管理器 - 用于临时密钥认证的全局存储.

This module provides a global in-memory storage for tmpkey authentication.
TmpKey is a 32-character random string that can be used as an alternative to JWT tokens.
"""
import secrets
import time
from typing import Dict, Optional
from threading import Lock

# 全局字典存储: {"tmpkey_xxx": {"user_id": "xxx", "expires_at": timestamp}}
TMPKEY_STORAGE: Dict[str, Dict[str, any]] = {}
STORAGE_LOCK = Lock()

# 默认过期时间：7天（与refresh token一致）
DEFAULT_EXPIRE_SECONDS = 7 * 24 * 60 * 60


def generate_tmpkey() -> str:
    """生成一个32字符的随机tmpkey.

    Returns:
        32字符的随机字符串（使用secrets.token_urlsafe，base64编码）
    """
    # token_urlsafe返回URL安全的base64编码字符串
    # 24字节会生成32个字符的base64字符串
    return secrets.token_urlsafe(24)


def store_tmpkey(tmpkey: str, user_id: str, expire_seconds: int = DEFAULT_EXPIRE_SECONDS) -> None:
    """存储tmpkey与user_id的映射关系.

    Args:
        tmpkey: 32字符的临时密钥
        user_id: 用户ID
        expire_seconds: 过期时间（秒），默认7天
    """
    with STORAGE_LOCK:
        expires_at = int(time.time()) + expire_seconds
        TMPKEY_STORAGE[tmpkey] = {
            "user_id": user_id,
            "expires_at": expires_at
        }


def get_user_id_by_tmpkey(tmpkey: str) -> Optional[str]:
    """通过tmpkey获取user_id.

    Args:
        tmpkey: 临时密钥

    Returns:
        用户ID，如果tmpkey不存在或已过期则返回None
    """
    with STORAGE_LOCK:
        data = TMPKEY_STORAGE.get(tmpkey)
        if not data:
            return None

        # 检查是否过期
        current_time = int(time.time())
        if current_time > data["expires_at"]:
            # 过期，删除存储
            del TMPKEY_STORAGE[tmpkey]
            return None

        return data["user_id"]


def remove_tmpkey(tmpkey: str) -> bool:
    """删除tmpkey（用户登出时使用）.

    Args:
        tmpkey: 要删除的临时密钥

    Returns:
        True如果删除成功，False如果tmpkey不存在
    """
    with STORAGE_LOCK:
        if tmpkey in TMPKEY_STORAGE:
            del TMPKEY_STORAGE[tmpkey]
            return True
        return False


def cleanup_expired_tmpkeys() -> int:
    """清理所有过期的tmpkey.

    Returns:
        清理的tmpkey数量
    """
    with STORAGE_LOCK:
        current_time = int(time.time())
        expired_keys = [
            key for key, value in TMPKEY_STORAGE.items()
            if current_time > value["expires_at"]
        ]

        for key in expired_keys:
            del TMPKEY_STORAGE[key]

        return len(expired_keys)


def get_tmpkey_count() -> int:
    """获取当前存储的tmpkey数量.

    Returns:
        存储的tmpkey总数
    """
    with STORAGE_LOCK:
        return len(TMPKEY_STORAGE)
