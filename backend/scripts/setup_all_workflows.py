#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置所有板块的 Dify 工作流
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.workflow import Workflow, WorkflowBinding
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

# 所有工作流配置（硬编码在代码中，部署后自动配置）
WORKFLOWS_CONFIG = [
    # 1. 单文件数据分析
    {
        "name": "运营数据分析工作流",
        "category": "operation",
        "function_key": "operation_data_analysis",
        "sheet_index": None,  # 非定制化批量分析
        "description": "单文件数据分析工作流",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-G5TRX6MyLsQdfj4V4NRWAplZ",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    # 2. 批量数据分析（使用相同的工作流）
    {
        "name": "批量数据分析工作流",
        "category": "operation",
        "function_key": "operation_batch_analysis",
        "sheet_index": None,
        "description": "批量数据分析工作流",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-G5TRX6MyLsQdfj4V4NRWAplZ",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    # 3-8. 定制化批量分析的6个工作流（Sheet 0-5）
    {
        "name": "最后操作分布工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 0,
        "description": "定制化批量分析 - Sheet 0（最后操作分布）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-bPuA3gTwoFUefEd9BYJexJ3l",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    {
        "name": "新手漏斗工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 1,
        "description": "定制化批量分析 - Sheet 1（新手漏斗）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-sAIJG3ZFzdgIS82JbmRne4sX",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    {
        "name": "回流用户工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 2,
        "description": "定制化批量分析 - Sheet 2（回流用户）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-1kzCXNaI1995gPPE3b9VATYr",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    {
        "name": "流失用户属性工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 3,
        "description": "定制化批量分析 - Sheet 3（流失用户属性）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-F9cfBnTx0A6cvUzwCEps9KFN",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    {
        "name": "留存率分析工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 4,
        "description": "定制化批量分析 - Sheet 4（留存率）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-DDrJ34dOessai3io1zcvtq7n",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    },
    {
        "name": "LTV分析工作流",
        "category": "operation",
        "function_key": "custom_operation_data_analysis",
        "sheet_index": 5,
        "description": "定制化批量分析 - Sheet 5（LTV）",
        "config": {
            "api_url": "http://118.89.16.95/v1",
            "api_key": "app-EUzFTWScRAOV2a0AlT2AvRLm",
            "url_file": "http://118.89.16.95/v1/files/upload",
            "url_work": "http://118.89.16.95/v1/chat-messages",
            "file_param": "excell",
            "query_param": "query",
            "workflow_id": "1",
            "workflow_type": "chatflow",
            "input_field": "excell,query"
        }
    }
]

def setup_all_workflows(user_id: int = 1):
    """配置所有工作流"""
    db = SessionLocal()
    
    try:
        created_count = 0
        updated_count = 0
        binding_count = 0
        
        for wf_config in WORKFLOWS_CONFIG:
            function_key = wf_config["function_key"]
            sheet_index = wf_config.get("sheet_index")
            
            # 查找或创建工作流
            workflow = db.query(Workflow).filter(
                Workflow.name == wf_config["name"],
                Workflow.category == wf_config["category"]
            ).first()
            
            if workflow:
                # 更新现有工作流
                workflow.config = wf_config["config"]
                workflow.description = wf_config["description"]
                workflow.is_active = True
                workflow.updated_at = datetime.utcnow()
                flag_modified(workflow, "config")
                updated_count += 1
                print(f"✓ 更新工作流: {wf_config['name']}")
            else:
                # 创建新工作流
                workflow = Workflow(
                    name=wf_config["name"],
                    category=wf_config["category"],
                    platform="dify",
                    config=wf_config["config"],
                    description=wf_config["description"],
                    is_active=True,
                    created_by=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(workflow)
                db.flush()  # 获取ID
                created_count += 1
                print(f"✓ 创建工作流: {wf_config['name']} (ID: {workflow.id})")
            
            # 查找或创建绑定（全局配置，user_id=None）
            query = db.query(WorkflowBinding).filter(
                WorkflowBinding.function_key == function_key,
                WorkflowBinding.user_id.is_(None)  # 全局配置
            )
            
            # 对于定制化批量分析，需要匹配sheet_index
            if sheet_index is not None:
                query = query.filter(WorkflowBinding.sheet_index == sheet_index)
            else:
                query = query.filter(WorkflowBinding.sheet_index.is_(None))
            
            binding = query.first()
            
            if binding:
                # 更新现有绑定
                binding.workflow_id = workflow.id
                binding.updated_at = datetime.utcnow()
                binding_count += 1
                sheet_info = f" (Sheet {sheet_index})" if sheet_index is not None else ""
                print(f"  ✓ 更新绑定: {function_key}{sheet_info} -> {workflow.id}")
            else:
                # 创建新绑定
                binding = WorkflowBinding(
                    workflow_id=workflow.id,
                    function_key=function_key,
                    user_id=None,  # 全局配置
                    sheet_index=sheet_index,  # 定制化批量分析需要sheet_index
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(binding)
                binding_count += 1
                sheet_info = f" (Sheet {sheet_index})" if sheet_index is not None else ""
                print(f"  ✓ 创建绑定: {function_key}{sheet_info} -> {workflow.id}")
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"配置完成！")
        print(f"  创建工作流: {created_count} 个")
        print(f"  更新工作流: {updated_count} 个")
        print(f"  配置绑定: {binding_count} 个")
        print(f"{'='*60}\n")
        
        # 显示所有配置
        print("已配置的工作流列表：")
        workflows = db.query(Workflow).filter(Workflow.category == "operation").all()
        for wf in workflows:
            bindings = db.query(WorkflowBinding).filter(
                WorkflowBinding.workflow_id == wf.id,
                WorkflowBinding.user_id.is_(None)
            ).all()
            function_keys = [b.function_key for b in bindings]
            print(f"  [{wf.id}] {wf.name}")
            print(f"      API Key: {wf.config.get('api_key', 'N/A')}")
            print(f"      功能键: {', '.join(function_keys)}")
            print()
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("开始配置所有 Dify 工作流...")
    print("="*60)
    print()
    
    success = setup_all_workflows()
    
    if success:
        print("\n✅ 所有工作流配置成功！")
        sys.exit(0)
    else:
        print("\n❌ 工作流配置失败！")
        sys.exit(1)









