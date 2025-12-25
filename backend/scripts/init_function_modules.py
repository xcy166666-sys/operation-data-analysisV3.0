"""
初始化功能模块数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.function_module import FunctionModule


def init_function_modules():
    """初始化功能模块数据"""
    db: Session = SessionLocal()
    try:
        # 检查是否已存在数据
        existing = db.query(FunctionModule).count()
        if existing > 0:
            print(f"功能模块数据已存在（共 {existing} 条），跳过初始化")
            return
        
        # 插入初始数据
        functions = [
            FunctionModule(
                function_key="operation_data_analysis",
                name="单文件数据分析",
                description="上传单个Excel文件，快速生成数据分析报告",
                route_path="/operation",
                icon="Document",
                category="operation",
                is_enabled=True,
                sort_order=1
            ),
            FunctionModule(
                function_key="operation_batch_analysis",
                name="批量数据分析",
                description="上传包含多个Sheet的Excel文件，批量生成分析报告",
                route_path="/operation/batch",
                icon="Files",
                category="operation",
                is_enabled=True,
                sort_order=2
            ),
            FunctionModule(
                function_key="custom_operation_data_analysis",
                name="黄伟斌定制款数据分析工具",
                description="定制化批量分析，支持根据Sheet索引自动选择工作流",
                route_path="/operation/custom-batch",
                icon="Setting",
                category="operation",
                is_enabled=True,
                sort_order=3
            )
        ]
        
        for func in functions:
            db.add(func)
        
        db.commit()
        print("✅ 功能模块数据初始化成功")
        print(f"   共创建 {len(functions)} 个功能模块")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_function_modules()

