#!/usr/bin/env python3
"""测试 httpx 连接到阿里云 DashScope API"""
import httpx
import asyncio

async def test_connection():
    """测试连接"""
    print("=" * 60)
    print("测试 httpx 连接到 DashScope API")
    print("=" * 60)
    
    # 测试 DNS 解析
    import socket
    try:
        ip = socket.gethostbyname('dashscope.aliyuncs.com')
        print(f"✓ DNS 解析成功: dashscope.aliyuncs.com -> {ip}")
    except Exception as e:
        print(f"✗ DNS 解析失败: {e}")
        return
    
    # 测试 HTTP 连接（不使用代理）
    try:
        # 使用更长的超时时间
        timeout = httpx.Timeout(30.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout, trust_env=False, verify=False) as client:
            print("\n正在测试 HTTPS 连接（trust_env=False, verify=False, timeout=30s）...")
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"✓ HTTP 连接成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"✗ HTTP 连接失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_connection())
