#!/usr/bin/env python3
"""详细测试 httpx 的 DNS 解析问题"""
import httpx
import asyncio
import socket

async def test_detailed():
    """详细测试"""
    print("=" * 60)
    print("详细测试 httpx DNS 解析")
    print("=" * 60)
    
    # 1. 测试标准库 DNS 解析
    print("\n1. 标准库 socket.gethostbyname():")
    try:
        ip = socket.gethostbyname('dashscope.aliyuncs.com')
        print(f"   ✓ 成功: {ip}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 2. 测试 socket.getaddrinfo()
    print("\n2. 标准库 socket.getaddrinfo():")
    try:
        result = socket.getaddrinfo('dashscope.aliyuncs.com', 443, socket.AF_INET, socket.SOCK_STREAM)
        print(f"   ✓ 成功: {result[0][4][0]}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 3. 测试直接使用 IP 地址
    print("\n3. httpx 直接使用 IP 地址:")
    try:
        timeout = httpx.Timeout(30.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout, trust_env=False, verify=False) as client:
            # 使用 IP 地址，但设置 Host 头
            headers = {'Host': 'dashscope.aliyuncs.com'}
            resp = await client.get('https://182.92.133.45', headers=headers)
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 4. 测试 httpx 使用域名（默认设置）
    print("\n4. httpx 使用域名（默认设置）:")
    try:
        timeout = httpx.Timeout(30.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 5. 测试 httpx 使用域名（trust_env=False）
    print("\n5. httpx 使用域名（trust_env=False）:")
    try:
        timeout = httpx.Timeout(30.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 6. 检查环境变量
    print("\n6. 环境变量:")
    import os
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy']:
        value = os.environ.get(key)
        if value:
            print(f"   {key}={value}")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_detailed())
