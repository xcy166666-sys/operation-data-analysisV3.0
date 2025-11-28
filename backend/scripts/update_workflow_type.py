"""
更新工作流类型为workflow（因为输入变量是excell和sys.query）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.workflow_service import WorkflowService

def update_workflow_type():
    """更新工作流类型为workflow"""
    db = SessionLocal()
    try:
        workflow = WorkflowService.get_workflow_by_id(db, 1)
        if not workflow:
            print("工作流不存在")
            return False
        
        current_type = workflow.config.get("workflow_type")
        print(f"当前工作流类型: {current_type}")
        
        if current_type != "workflow":
            # 创建新的配置字典
            new_config = dict(workflow.config)
            new_config["workflow_type"] = "workflow"
            # 使用flag_modified标记JSONB字段已修改
            from sqlalchemy.orm.attributes import flag_modified
            workflow.config = new_config
            flag_modified(workflow, "config")
            db.commit()
            db.refresh(workflow)
            print("已修改为workflow类型")
        else:
            print("工作流类型已经是workflow，无需修改")
        
        # 重新查询以确保获取最新数据
        db.refresh(workflow)
        print(f"更新后的配置: {workflow.config}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("开始更新工作流类型...")
    success = update_workflow_type()
    
    if success:
        print("\n[成功] 工作流类型更新成功！")
        sys.exit(0)
    else:
        print("\n[失败] 工作流类型更新失败！")
        sys.exit(1)

