#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证工作流配置"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.workflow import Workflow, WorkflowBinding

db = SessionLocal()

print("="*60)
print("工作流配置验证")
print("="*60)
print()

# 检查单文件分析工作流
binding = db.query(WorkflowBinding).filter(
    WorkflowBinding.function_key == 'operation_data_analysis',
    WorkflowBinding.user_id.is_(None)
).first()

if binding:
    wf = binding.workflow
    print(f"✅ 单文件分析工作流配置:")
    print(f"   名称: {wf.name}")
    print(f"   API Key: {wf.config.get('api_key')}")
    print(f"   文件上传URL: {wf.config.get('url_file')}")
    print(f"   工作流URL: {wf.config.get('url_work')}")
    print(f"   状态: {'激活' if wf.is_active else '未激活'}")
    print()
else:
    print("❌ 未找到单文件分析工作流配置")
    print()

# 检查所有工作流
workflows = db.query(Workflow).filter(Workflow.category == "operation").all()
print(f"总共配置了 {len(workflows)} 个工作流:")
for wf in workflows:
    bindings = db.query(WorkflowBinding).filter(
        WorkflowBinding.workflow_id == wf.id,
        WorkflowBinding.user_id.is_(None)
    ).all()
    function_keys = [b.function_key for b in bindings]
    status = "✅" if wf.is_active else "❌"
    print(f"  {status} [{wf.id}] {wf.name}")
    print(f"     功能键: {', '.join(function_keys) if function_keys else '无'}")
    print(f"     API Key: {wf.config.get('api_key', 'N/A')}")

db.close()









