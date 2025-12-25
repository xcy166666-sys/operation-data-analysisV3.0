"""
更新工作流配置（使用新的 url_file 和 url_work 格式）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.workflow_service import WorkflowService

# 新的 Dify 工作流配置
NEW_CONFIG = {
    "api_key": "app-G5TRX6MyLsQdfj4V4NRWAplZ",
    "url_file": "http://118.89.16.95/v1/files/upload",
    "url_work": "http://118.89.16.95/v1/chat-messages",
    "file_param": "excell",
    "query_param": "query",
    "workflow_id": "1",
    "workflow_type": "chatflow",
    "input_field": "excell,query"
}

def update_workflow_config():
    """更新工作流配置"""
    db = SessionLocal()
    try:
        # 查找运营数据分析工作流
        workflows = WorkflowService.get_workflows(
            db, 
            category="operation",
            platform="dify"
        )
        
        workflow = None
        for wf in workflows:
            if wf.name == "运营数据分析工作流":
                workflow = wf
                break
        
        if not workflow:
            print("未找到'运营数据分析工作流'，请先创建")
            return False
        
        print(f"找到工作流: ID={workflow.id}, Name={workflow.name}")
        print(f"当前配置: {workflow.config}")
        
        # 更新配置
        from sqlalchemy.orm.attributes import flag_modified
        new_config = dict(workflow.config) if workflow.config else {}
        new_config.update(NEW_CONFIG)
        
        workflow.config = new_config
        flag_modified(workflow, "config")
        db.commit()
        db.refresh(workflow)
        
        print(f"\n更新后的配置:")
        print(f"  API Key: {workflow.config.get('api_key')}")
        print(f"  文件上传URL: {workflow.config.get('url_file')}")
        print(f"  工作流URL: {workflow.config.get('url_work')}")
        print(f"  文件参数名: {workflow.config.get('file_param')}")
        print(f"  对话参数名: {workflow.config.get('query_param')}")
        print(f"  工作流类型: {workflow.config.get('workflow_type')}")
        
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
    print("开始更新工作流配置...")
    success = update_workflow_config()
    
    if success:
        print("\n[成功] 工作流配置更新成功！")
        sys.exit(0)
    else:
        print("\n[失败] 工作流配置更新失败！")
        sys.exit(1)










