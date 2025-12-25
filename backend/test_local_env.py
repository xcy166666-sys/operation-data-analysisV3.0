#!/usr/bin/env python3
"""测试本地开发环境配置"""
import sys
import os

# 设置使用本地环境变量
os.environ["ENV_FILE"] = ".env.local"

print("=" * 60)
print("测试本地开发环境")
print("=" * 60)

# 1. 测试配置加载
print("\n1. 测试配置加载:")
try:
    from app.core.config import settings
    print(f"   ✓ 配置加载成功")
    print(f"   - APP_NAME: {settings.APP_NAME}")
    print(f"   - DEBUG: {settings.DEBUG}")
    print(f"   - DATABASE_URL: {settings.database_url[:50]}...")
    print(f"   - REDIS_URL: {settings.REDIS_URL}")
    print(f"   - DASHSCOPE_API_KEY: {'已配置' if settings.DASHSCOPE_API_KEY else '未配置'}")
except Exception as e:
    print(f"   ✗ 配置加载失败: {e}")
    sys.exit(1)

# 2. 测试数据库连接
print("\n2. 测试数据库连接:")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✓ 数据库连接成功")
        print(f"   - PostgreSQL 版本: {version[:50]}...")
except Exception as e:
    print(f"   ✗ 数据库连接失败: {e}")

# 3. 测试 Redis 连接
print("\n3. 测试 Redis 连接:")
try:
    import redis
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    print(f"   ✓ Redis 连接成功")
except Exception as e:
    print(f"   ✗ Redis 连接失败: {e}")

# 4. 测试 httpx 网络连接
print("\n4. 测试 httpx 网络连接:")
try:
    import httpx
    import asyncio
    
    async def test_httpx():
        timeout = httpx.Timeout(10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            return resp.status_code
    
    status = asyncio.run(test_httpx())
    print(f"   ✓ httpx 连接成功: 状态码 {status}")
except Exception as e:
    print(f"   ✗ httpx 连接失败: {type(e).__name__}: {e}")

# 5. 测试 DNS 解析
print("\n5. 测试 DNS 解析:")
try:
    import socket
    ip = socket.gethostbyname('dashscope.aliyuncs.com')
    print(f"   ✓ DNS 解析成功: dashscope.aliyuncs.com -> {ip}")
except Exception as e:
    print(f"   ✗ DNS 解析失败: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
