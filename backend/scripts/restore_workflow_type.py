"""
恢复工作流类型为workflow（base64编码方式，不需要上传文件）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.workflow_service import WorkflowService

def restore_workflow_type():
    """恢复工作流类型为workflow"""
    db = SessionLocal()
    try:
        workflow = WorkflowService.get_workflow_by_id(db, 1)
        if not workflow:
            print("工作流不存在")
            return False
        
        print(f"当前配置: {workflow.config}")
        
        # 恢复为workflow类型配置
        new_config = dict(workflow.config)
        new_config["workflow_type"] = "workflow"  # 改回workflow
        new_config["input_field"] = "excell,sys.query"  # 输入变量：excell和sys.query
        
        # 使用flag_modified标记JSONB字段已修改
        from sqlalchemy.orm.attributes import flag_modified
        workflow.config = new_config
        flag_modified(workflow, "config")
        db.commit()
        db.refresh(workflow)
        
        print("\n恢复后的配置:")
        print(f"  工作流类型: {workflow.config.get('workflow_type')}")
        print(f"  输入字段: {workflow.config.get('input_field')}")
        print(f"  API地址: {workflow.config.get('api_url')}")
        print(f"  工作流ID: {workflow.config.get('workflow_id')}")
        print(f"  API Key: {workflow.config.get('api_key')[:20]}...")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"恢复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("开始恢复工作流类型为workflow...")
    success = restore_workflow_type()
    
    if success:
        print("\n[成功] 工作流类型已恢复为workflow！")
        print("注意: 保持get_current_active_user，需要登录验证")
        sys.exit(0)
    else:
        print("\n[失败] 工作流类型恢复失败！")
        sys.exit(1)

