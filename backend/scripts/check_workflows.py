#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查工作流配置"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.workflow import Workflow, WorkflowBinding

db = SessionLocal()

print("="*60)
print("工作流配置检查")
print("="*60)
print()

# 检查批量分析工作流
print("1. 批量数据分析工作流:")
binding = db.query(WorkflowBinding).filter(
    WorkflowBinding.function_key == 'operation_data_analysis',
    WorkflowBinding.user_id.is_(None)
).first()

if binding:
    wf = binding.workflow
    print(f"   ✅ 已配置")
    print(f"   名称: {wf.name}")
    print(f"   API Key: {wf.config.get('api_key')}")
    print(f"   文件上传URL: {wf.config.get('url_file')}")
    print(f"   工作流URL: {wf.config.get('url_work')}")
    print(f"   状态: {'激活' if wf.is_active else '未激活'}")
else:
    print("   ❌ 未配置")

print()

# 检查定制化批量分析工作流
print("2. 定制化批量数据分析工作流:")
print("   注意：定制化批量分析使用硬编码配置，根据Sheet索引选择不同工作流")
print()
print("   Sheet 0 (最后操作分布):")
print("     API Key: app-bPuA3gTwoFUefEd9BYJexJ3l")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()
print("   Sheet 1 (新手漏斗):")
print("     API Key: app-sAIJG3ZFzdgIS82JbmRne4sX")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()
print("   Sheet 2 (回流用户):")
print("     API Key: app-1kzCXNaI1995gPPE3b9VATYr")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()
print("   Sheet 3 (流失用户属性):")
print("     API Key: app-F9cfBnTx0A6cvUzwCEps9KFN")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()
print("   Sheet 4 (留存率):")
print("     API Key: app-DDrJ34dOessai3io1zcvtq7n")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()
print("   Sheet 5 (LTV):")
print("     API Key: app-EUzFTWScRAOV2a0AlT2AvRLm")
print("     文件上传URL: http://118.89.16.95/v1/files/upload")
print("     工作流URL: http://118.89.16.95/v1/chat-messages")
print()

db.close()





