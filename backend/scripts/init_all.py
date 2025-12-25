#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整初始化脚本：初始化功能模块和工作流配置
用于新部署环境的数据初始化（自动运行）
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.function_module import FunctionModule
from app.models.workflow import WorkflowBinding
from scripts.init_function_modules import init_function_modules
from scripts.setup_all_workflows import setup_all_workflows


def init_all(user_id: int = 1):
    """完整初始化：功能模块 + 工作流配置"""
    print("="*60)
    print("开始初始化数据库...")
    print("="*60)
    print()
    
    db = SessionLocal()
    
    try:
        # 1. 初始化功能模块
        print("步骤 1/2: 初始化功能模块...")
        init_function_modules()
        print()
        
        # 2. 初始化工作流配置
        print("步骤 2/2: 初始化工作流配置...")
        success = setup_all_workflows(user_id=user_id)
        print()
        
        if not success:
            print("⚠️  工作流配置失败，但功能模块已初始化")
            return False
        
        # 3. 验证配置
        print("验证配置...")
        bindings_count = db.query(WorkflowBinding).filter(
            WorkflowBinding.user_id.is_(None)
        ).count()
        
        functions_count = db.query(FunctionModule).count()
        
        print(f"✅ 初始化完成！")
        print(f"   功能模块: {functions_count} 个")
        print(f"   工作流绑定: {bindings_count} 个")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = init_all()
    sys.exit(0 if success else 1)

