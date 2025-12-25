"""检查API配置"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

print("=" * 50)
print("API配置检查")
print("=" * 50)

# 检查阿里百炼API
print("\n1. 阿里百炼DashScope API:")
if settings.DASHSCOPE_API_KEY:
    print(f"   ✅ API Key: {settings.DASHSCOPE_API_KEY[:25]}...")
    print(f"   ✅ Model: {settings.DASHSCOPE_MODEL}")
    if settings.DASHSCOPE_API_BASE:
        print(f"   ✅ API Base: {settings.DASHSCOPE_API_BASE}")
else:
    print("   ❌ API Key: 未配置")

# 检查Dify API
print("\n2. Dify API:")
if settings.DIFY_API_KEY:
    print(f"   ✅ API Key: {settings.DIFY_API_KEY[:25]}...")
    print(f"   ✅ API URL: {settings.DIFY_API_URL}")
else:
    print("   ⚠️  API Key: 未配置（可通过管理界面配置）")

print("\n" + "=" * 50)


