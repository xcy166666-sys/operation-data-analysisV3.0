#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查各个功能板块的API配置情况"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.function_module import FunctionModule
from app.models.workflow import Workflow, WorkflowBinding

db = SessionLocal()

print("="*80)
print("功能板块API配置检查报告")
print("="*80)
print()

# 定义三个功能模块
FUNCTION_MODULES = [
    {
        "function_key": "operation_data_analysis",
        "name": "单文件数据分析",
        "description": "上传单个Excel文件，快速生成数据分析报告"
    },
    {
        "function_key": "operation_batch_analysis",
        "name": "批量数据分析",
        "description": "上传包含多个Sheet的Excel文件，批量生成分析报告"
    },
    {
        "function_key": "custom_operation_data_analysis",
        "name": "黄伟斌定制款数据分析工具",
        "description": "定制化批量分析，支持根据Sheet索引自动选择工作流"
    }
]

# 检查每个功能模块
for idx, func_info in enumerate(FUNCTION_MODULES, 1):
    function_key = func_info["function_key"]
    function_name = func_info["name"]
    
    print(f"{idx}. {function_name} ({function_key})")
    print("-" * 80)
    
    # 检查功能模块是否存在
    func_module = db.query(FunctionModule).filter(
        FunctionModule.function_key == function_key
    ).first()
    
    if not func_module:
        print(f"   ❌ 功能模块不存在")
        print()
        continue
    
    # 显示功能模块基本信息
    status_icon = "✅" if func_module.is_enabled else "❌"
    print(f"   功能状态: {status_icon} {'启用' if func_module.is_enabled else '禁用'}")
    print(f"   路由路径: {func_module.route_path or '-'}")
    print(f"   描述: {func_module.description or '-'}")
    
    # 检查工作流配置
    if function_key == "custom_operation_data_analysis":
        # 定制化批量分析：需要检查6个工作流配置（sheet_index 0-5）
        print(f"\n   工作流配置（需要6个，对应Sheet索引0-5）:")
        
        bindings = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None),  # 全局配置
            WorkflowBinding.sheet_index.isnot(None)
        ).order_by(WorkflowBinding.sheet_index).all()
        
        if not bindings:
            print(f"   ❌ 未配置任何工作流")
        else:
            configured_indices = set(binding.sheet_index for binding in bindings)
            required_indices = {0, 1, 2, 3, 4, 5}
            missing_indices = required_indices - configured_indices
            
            if missing_indices:
                print(f"   ⚠️  部分配置（已配置: {sorted(configured_indices)}, 缺失: {sorted(missing_indices)}）")
            else:
                print(f"   ✅ 已完整配置6个工作流")
            
            print()
            for binding in bindings:
                workflow = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
                if workflow:
                    status_icon = "✅" if workflow.is_active else "❌"
                    print(f"   Sheet {binding.sheet_index}:")
                    print(f"     状态: {status_icon} {'激活' if workflow.is_active else '未激活'}")
                    print(f"     工作流ID: {workflow.id}")
                    print(f"     工作流名称: {workflow.name}")
                    print(f"     平台: {workflow.platform}")
                    if workflow.config:
                        config = workflow.config
                        api_key = config.get("api_key", "N/A")
                        # 只显示API Key的前10个字符和后5个字符
                        if api_key != "N/A" and len(api_key) > 15:
                            api_key_display = f"{api_key[:10]}...{api_key[-5:]}"
                        else:
                            api_key_display = api_key
                        print(f"     API Key: {api_key_display}")
                        print(f"     文件上传URL: {config.get('url_file', config.get('api_url', 'N/A'))}")
                        print(f"     工作流URL: {config.get('url_work', config.get('api_url', 'N/A'))}")
                    print()
    else:
        # 其他功能：检查单个工作流配置
        print(f"\n   工作流配置:")
        
        binding = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == function_key,
            WorkflowBinding.user_id.is_(None),  # 全局配置
            WorkflowBinding.sheet_index.is_(None)  # 非定制化批量分析
        ).first()
        
        if not binding:
            print(f"   ❌ 未配置工作流")
        else:
            workflow = db.query(Workflow).filter(Workflow.id == binding.workflow_id).first()
            if workflow:
                status_icon = "✅" if workflow.is_active else "❌"
                print(f"   {status_icon} 已配置")
                print(f"     工作流ID: {workflow.id}")
                print(f"     工作流名称: {workflow.name}")
                print(f"     平台: {workflow.platform}")
                print(f"     状态: {'激活' if workflow.is_active else '未激活'}")
                if workflow.config:
                    config = workflow.config
                    api_key = config.get("api_key", "N/A")
                    # 只显示API Key的前10个字符和后5个字符
                    if api_key != "N/A" and len(api_key) > 15:
                        api_key_display = f"{api_key[:10]}...{api_key[-5:]}"
                    else:
                        api_key_display = api_key
                    print(f"     API Key: {api_key_display}")
                    print(f"     文件上传URL: {config.get('url_file', config.get('api_url', 'N/A'))}")
                    print(f"     工作流URL: {config.get('url_work', config.get('api_url', 'N/A'))}")
                    print(f"     文件参数名: {config.get('file_param', 'excell')}")
                    print(f"     查询参数名: {config.get('query_param', 'query')}")
            else:
                print(f"   ❌ 工作流不存在（绑定ID: {binding.workflow_id}）")
    
    print()

# 统计信息
print("="*80)
print("统计信息")
print("="*80)

total_modules = db.query(FunctionModule).count()
enabled_modules = db.query(FunctionModule).filter(FunctionModule.is_enabled == True).count()
total_workflows = db.query(Workflow).count()
active_workflows = db.query(Workflow).filter(Workflow.is_active == True).count()
total_bindings = db.query(WorkflowBinding).filter(WorkflowBinding.user_id.is_(None)).count()

print(f"功能模块总数: {total_modules}")
print(f"已启用功能: {enabled_modules}")
print(f"工作流总数: {total_workflows}")
print(f"激活工作流: {active_workflows}")
print(f"全局工作流绑定: {total_bindings}")

# 检查用户级配置
user_bindings = db.query(WorkflowBinding).filter(WorkflowBinding.user_id.isnot(None)).count()
if user_bindings > 0:
    print(f"用户级工作流绑定: {user_bindings}")

print()
print("="*80)

db.close()

