#!/usr/bin/env python3
"""测试使用代理的 httpx"""
import httpx
import asyncio

async def test():
    print("=" * 60)
    print("测试使用代理的 httpx")
    print("=" * 60)
    
    # 尝试使用本地代理
    proxy = "http://127.0.0.1:7890"
    
    print(f"\n使用代理: {proxy}")
    
    # 1. 测试百度
    print("\n1. 测试百度:")
    try:
        proxies = {"http://": proxy, "https://": proxy}
        async with httpx.AsyncClient(timeout=10.0, proxies=proxies) as client:
            resp = await client.get('https://www.baidu.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    # 2. 测试阿里云
    print("\n2. 测试阿里云 DashScope:")
    try:
        proxies = {"http://": proxy, "https://": proxy}
        async with httpx.AsyncClient(timeout=10.0, proxies=proxies) as client:
            resp = await client.get('https://dashscope.aliyuncs.com')
            print(f"   ✓ 成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
