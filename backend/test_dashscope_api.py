#!/usr/bin/env python3
"""测试阿里云 DashScope API 调用"""
import httpx
import asyncio
import os

# 设置使用本地环境变量
os.environ["ENV_FILE"] = ".env.local"

from app.core.config import settings

async def test():
    print("=" * 60)
    print("测试阿里云 DashScope API")
    print("=" * 60)
    
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    api_key = settings.DASHSCOPE_API_KEY
    
    if not api_key:
        print("\n✗ DASHSCOPE_API_KEY 未配置")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "你好"
                }
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    # 测试不同的配置
    configs = [
        ("默认设置", {}),
        ("trust_env=False", {"trust_env": False}),
        ("使用代理", {"proxies": {"http://": "http://127.0.0.1:7890", "https://": "http://127.0.0.1:7890"}}),
    ]
    
    for name, kwargs in configs:
        print(f"\n{name}:")
        try:
            async with httpx.AsyncClient(timeout=30.0, **kwargs) as client:
                resp = await client.post(api_url, json=payload, headers=headers)
                print(f"   ✓ 成功: 状态码 {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    if 'output' in data and 'choices' in data['output']:
                        content = data['output']['choices'][0]['message']['content']
                        print(f"   - 响应: {content[:50]}...")
                else:
                    print(f"   - 响应: {resp.text[:100]}")
                break  # 成功后退出
        except Exception as e:
            print(f"   ✗ 失败: {type(e).__name__}: {str(e)[:100]}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
