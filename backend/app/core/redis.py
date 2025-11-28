"""
Redis连接和缓存管理（可选）
"""
from typing import Optional, Any
import json
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """Redis客户端封装"""
    
    def __init__(self):
        self._client: Optional[Redis] = None
    
    async def connect(self) -> None:
        """连接Redis"""
        try:
            self._client = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
        except Exception as e:
            # Redis是可选的，连接失败不影响主功能
            print(f"Redis连接失败（可选服务）: {e}")
            self._client = None
    
    async def disconnect(self) -> None:
        """断开Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
    
    @property
    def client(self) -> Optional[Redis]:
        """获取Redis客户端"""
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self._client:
            return None
        return await self._client.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """
        设置值
        
        Args:
            key: 键
            value: 值（如果是dict/list会自动JSON序列化）
            expire: 过期时间（秒），None表示永不过期
        """
        if not self._client:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        await self._client.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> None:
        """删除键"""
        if not self._client:
            return
        await self._client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._client:
            return False
        return await self._client.exists(key) > 0
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """
        设置JSON值（便捷方法）
        
        Args:
            key: 键
            value: 值（dict/list，会自动JSON序列化）
            expire: 过期时间（秒），None表示永不过期
        """
        await self.set(key, value, expire=expire)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """
        获取JSON值（便捷方法）
        
        Args:
            key: 键
            
        Returns:
            反序列化后的值，如果不存在返回None
        """
        if not self._client:
            return None
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，返回原始值
            return value


# 创建全局Redis客户端实例
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """
    获取Redis客户端
    
    用于FastAPI依赖注入:
    
    @app.get("/cache")
    async def get_cache(redis: RedisClient = Depends(get_redis)):
        return await redis.get("key")
    """
    return redis_client

