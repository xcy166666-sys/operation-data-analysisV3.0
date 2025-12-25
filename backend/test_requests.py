#!/usr/bin/env python3
"""测试 requests 库连接"""
import requests

def test_requests():
    """测试 requests"""
    print("=" * 60)
    print("测试 requests 库连接")
    print("=" * 60)
    
    try:
        print("\n正在测试 HTTPS 连接...")
        resp = requests.get('https://dashscope.aliyuncs.com', timeout=30)
        print(f"✓ 连接成功: 状态码 {resp.status_code}")
    except Exception as e:
        print(f"✗ 连接失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_requests()
