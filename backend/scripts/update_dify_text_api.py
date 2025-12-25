"""
更新Dify文本生成API配置
将运营数据分析工作流的API Key更新为新的值
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.workflow import Workflow, WorkflowBinding
from sqlalchemy.orm.attributes import flag_modified
from loguru import logger

# 新的API Key
NEW_API_KEY = "app-2i0887SmxI5cn4q7QGv7OpMg"

def update_dify_text_api():
    """更新Dify文本生成API配置"""
    db = SessionLocal()
    try:
        # 查找运营数据分析工作流绑定
        binding = db.query(WorkflowBinding).filter(
            WorkflowBinding.function_key == "operation_data_analysis",
            WorkflowBinding.user_id.is_(None)  # 全局配置
        ).first()
        
        if not binding:
            print("❌ 未找到'运营数据分析'工作流绑定")
            print("   请先通过管理界面配置工作流")
            return False
        
        workflow = binding.workflow
        if not workflow:
            print("❌ 工作流不存在")
            return False
        
        print(f"✅ 找到工作流: ID={workflow.id}, Name={workflow.name}")
        print(f"   当前API Key: {workflow.config.get('api_key') if workflow.config else 'None'}")
        
        # 更新配置
        if not workflow.config:
            workflow.config = {}
        
        new_config = dict(workflow.config)
        old_api_key = new_config.get("api_key", "未配置")
        new_config["api_key"] = NEW_API_KEY
        
        workflow.config = new_config
        flag_modified(workflow, "config")
        db.commit()
        db.refresh(workflow)
        
        print(f"\n✅ 更新成功！")
        print(f"   旧API Key: {old_api_key}")
        print(f"   新API Key: {workflow.config.get('api_key')}")
        print(f"\n完整配置:")
        print(f"   API地址: {workflow.config.get('api_url', '未配置')}")
        print(f"   API Key: {workflow.config.get('api_key')}")
        print(f"   文件上传URL: {workflow.config.get('url_file', '未配置')}")
        print(f"   工作流URL: {workflow.config.get('url_work', '未配置')}")
        print(f"   工作流类型: {workflow.config.get('workflow_type', '未配置')}")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新失败: {str(e)}")
        print(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("更新Dify文本生成API配置")
    print("=" * 60)
    print(f"新API Key: {NEW_API_KEY}")
    print()
    
    success = update_dify_text_api()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 配置更新完成！")
        print("=" * 60)
        print("\n提示：")
        print("1. 如果还有其他工作流需要更新，请通过管理界面手动配置")
        print("2. 批量分析和定制化批量分析的工作流配置是独立的")
        print("3. 可以通过前端管理界面查看和修改所有工作流配置")
    else:
        print("\n" + "=" * 60)
        print("❌ 配置更新失败")
        print("=" * 60)


