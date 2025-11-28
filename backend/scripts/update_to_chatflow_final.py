"""
更新工作流配置为Chatflow类型（最终版本）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.workflow_service import WorkflowService

def update_to_chatflow():
    """更新工作流配置为Chatflow类型"""
    db = SessionLocal()
    try:
        workflow = WorkflowService.get_workflow_by_id(db, 1)
        if not workflow:
            print("工作流不存在")
            return False
        
        print(f"当前配置: {workflow.config}")
        
        # 更新为Chatflow配置
        new_config = dict(workflow.config)
        new_config["api_key"] = "app-G5TRX6MyLsQdfj4V4NRWAplZ"  # 新的API Key
        new_config["workflow_type"] = "chatflow"  # Chatflow类型
        new_config["input_field"] = "excell,query"  # 文件参数：excell，对话参数：query
        
        # 使用flag_modified标记JSONB字段已修改
        from sqlalchemy.orm.attributes import flag_modified
        workflow.config = new_config
        flag_modified(workflow, "config")
        db.commit()
        db.refresh(workflow)
        
        print("\n更新后的配置:")
        print(f"  API Key: {workflow.config.get('api_key')}")
        print(f"  工作流类型: {workflow.config.get('workflow_type')}")
        print(f"  输入字段: {workflow.config.get('input_field')}")
        print(f"  API地址: {workflow.config.get('api_url')}")
        print(f"  工作流ID: {workflow.config.get('workflow_id')}")
        print(f"\n文件上传URL: {workflow.config.get('api_url')}/files/upload")
        print(f"工作流URL: {workflow.config.get('api_url')}/chat-messages")
        
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
    print("开始更新工作流配置为Chatflow类型...")
    success = update_to_chatflow()
    
    if success:
        print("\n[成功] 工作流配置已更新为Chatflow！")
        print("注意: 保持get_current_active_user，需要登录验证")
        sys.exit(0)
    else:
        print("\n[失败] 工作流配置更新失败！")
        sys.exit(1)

