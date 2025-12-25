"""
手动添加 version_id 列到 dialog_histories 表
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from loguru import logger


def add_version_id_column():
    """添加 version_id 列"""
    db = SessionLocal()
    
    try:
        logger.info("开始添加 version_id 列...")
        
        # 检查列是否已存在
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'dialog_histories' 
            AND column_name = 'version_id'
        """)
        
        result = db.execute(check_sql).fetchone()
        
        if result:
            logger.info("version_id 列已存在，跳过添加")
            return
        
        # 添加列
        logger.info("添加 version_id 列...")
        add_column_sql = text("""
            ALTER TABLE dialog_histories 
            ADD COLUMN version_id INTEGER
        """)
        db.execute(add_column_sql)
        db.commit()
        logger.info("✅ version_id 列添加成功")
        
        # 添加外键约束
        logger.info("添加外键约束...")
        try:
            add_fk_sql = text("""
                ALTER TABLE dialog_histories 
                ADD CONSTRAINT fk_dialog_histories_version_id 
                FOREIGN KEY (version_id) 
                REFERENCES analysis_session_versions(id) 
                ON DELETE SET NULL
            """)
            db.execute(add_fk_sql)
            db.commit()
            logger.info("✅ 外键约束添加成功")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("外键约束已存在，跳过添加")
            else:
                raise
        
        # 验证
        logger.info("验证表结构...")
        verify_sql = text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'dialog_histories'
            ORDER BY ordinal_position
        """)
        
        columns = db.execute(verify_sql).fetchall()
        logger.info("dialog_histories 表结构:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        logger.info("✅ 迁移完成！")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_version_id_column()
