"""
API通用依赖项
"""
from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import get_db as _get_db
from app.core.redis import get_redis as _get_redis, RedisClient


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（重新导出以便API使用）"""
    yield from _get_db()


async def get_redis() -> RedisClient:
    """获取Redis客户端（重新导出以便API使用）"""
    return await _get_redis()

