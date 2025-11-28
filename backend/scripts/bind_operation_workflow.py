"""
绑定运营数据分析工作流（单项目系统版本）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowCreate
from app.models.user import User

# Dify 工作流配置（Chatflow类型）
WORKFLOW_CONFIG = {
    "name": "运营数据分析工作流",
    "api_url": "http://118.89.16.95/v1",
    "api_key": "app-G5TRX6MyLsQdfj4V4NRWAplZ",
    "workflow_id": "1",  # Chatflow ID
    "workflow_type": "chatflow",  # Chatflow类型
    "input_field": "excell,query",  # 文件参数：excell，对话参数：query
    "description": "运营数据分析工作流，用于分析Excel文件并生成报告"
}


def bind_workflow(user_id: int = 1):
    """
    绑定工作流到系统（单项目系统，不需要project_id）
    
    Args:
        user_id: 创建者用户ID（默认1，管理员）
    """
    db = SessionLocal()
    try:
        # 1. 检查是否已存在同名工作流
        existing_workflows = WorkflowService.get_workflows(
            db, 
            category="operation",
            platform="dify"
        )
        
        workflow = None
        for wf in existing_workflows:
            if wf.name == WORKFLOW_CONFIG["name"]:
                workflow = wf
                print(f"找到已存在的工作流: ID={workflow.id}, Name={workflow.name}")
                break
        
        # 2. 如果不存在，创建工作流
        if not workflow:
            workflow_data = WorkflowCreate(
                name=WORKFLOW_CONFIG["name"],
                category="operation",
                platform="dify",
                config={
                    "api_url": WORKFLOW_CONFIG["api_url"],
                    "api_key": WORKFLOW_CONFIG["api_key"],
                    "workflow_id": WORKFLOW_CONFIG["workflow_id"],
                    "workflow_type": WORKFLOW_CONFIG["workflow_type"],
                    "input_field": WORKFLOW_CONFIG["input_field"]
                },
                description=WORKFLOW_CONFIG["description"],
                is_active=True
            )
            
            workflow = WorkflowService.create_workflow(
                db, workflow_data, user_id
            )
            print(f"创建工作流成功: ID={workflow.id}, Name={workflow.name}")
        else:
            # 更新工作流配置
            workflow.config = {
                "api_url": WORKFLOW_CONFIG["api_url"],
                "api_key": WORKFLOW_CONFIG["api_key"],
                "workflow_id": WORKFLOW_CONFIG["workflow_id"],
                "workflow_type": WORKFLOW_CONFIG["workflow_type"],
                "input_field": WORKFLOW_CONFIG["input_field"]
            }
            db.commit()
            db.refresh(workflow)
            print(f"更新工作流配置成功: ID={workflow.id}")
        
        # 3. 绑定工作流到功能（单项目系统，不需要project_id）
        function_key = "operation_data_analysis"
        binding = WorkflowService.bind_function_workflow(
            db,
            function_key,
            workflow.id
        )
        
        print(f"\n绑定工作流成功:")
        print(f"  - 功能键: {function_key}")
        print(f"  - 工作流ID: {workflow.id}")
        print(f"  - 工作流名称: {workflow.name}")
        print(f"  - 工作流类型: {WORKFLOW_CONFIG['workflow_type']}")
        print(f"  - Dify API地址: {WORKFLOW_CONFIG['api_url']}")
        print(f"  - Dify工作流ID: {WORKFLOW_CONFIG['workflow_id']}")
        print(f"  - 输入变量: {WORKFLOW_CONFIG['input_field']}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"绑定工作流失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="绑定运营数据分析工作流（单项目系统）")
    parser.add_argument("--user-id", type=int, default=1, help="创建者用户ID（默认1）")
    
    args = parser.parse_args()
    
    print(f"开始绑定工作流...")
    success = bind_workflow(args.user_id)
    
    if success:
        print("\n[成功] 工作流绑定成功！")
        sys.exit(0)
    else:
        print("\n[失败] 工作流绑定失败！")
        sys.exit(1)

