#!/usr/bin/env python3
"""测试 Windows 本地环境中的 httpx"""
import httpx
import asyncio
import socket

async def test():
    print("=" * 60)
    print("测试 Windows 本地环境中的 httpx")
    print("=" * 60)
    
    # 1. DNS 解析
    print("\n1. DNS 解析:")
    try:
        ip = socket.gethostbyname('dashscope.aliyuncs.com')
        print(f"   ✓ 成功: {ip}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 2. httpx 默认设置
    print("\n2. httpx 默认设置:")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 3. httpx trust_env=False
    print("\n3. httpx trust_env=False:")
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 4. 测试百度（验证网络是否正常）
    print("\n4. 测试百度（验证网络）:")
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get('https://www.baidu.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
