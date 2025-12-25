"""
迁移脚本：将 AnalysisSession.messages 中的对话历史迁移到 DialogHistory 表
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.session import AnalysisSession
from app.models.dialog_history import DialogHistory
from loguru import logger


def migrate_dialog_history():
    """迁移对话历史数据"""
    db: Session = SessionLocal()
    
    try:
        logger.info("开始迁移对话历史数据...")
        
        # 获取所有有消息的会话
        sessions = db.query(AnalysisSession).filter(
            AnalysisSession.messages.isnot(None)
        ).all()
        
        logger.info(f"找到 {len(sessions)} 个会话需要迁移")
        
        migrated_count = 0
        skipped_count = 0
        
        for session in sessions:
            if not session.messages or len(session.messages) == 0:
                skipped_count += 1
                continue
            
            logger.info(f"迁移会话 {session.id} ({session.title}) - {len(session.messages)} 条消息")
            
            # 检查是否已经迁移过
            existing_count = db.query(DialogHistory).filter(
                DialogHistory.session_id == session.id
            ).count()
            
            if existing_count > 0:
                logger.warning(f"会话 {session.id} 已有 {existing_count} 条对话历史，跳过迁移")
                skipped_count += 1
                continue
            
            # 迁移每条消息
            for msg in session.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                timestamp_str = msg.get("timestamp")
                
                # 解析时间戳
                created_at = None
                if timestamp_str:
                    try:
                        from datetime import datetime
                        created_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if created_at.tzinfo:
                            created_at = created_at.replace(tzinfo=None)
                    except:
                        pass
                
                # 构建额外数据
                extra_data = {}
                if msg.get("modified_charts"):
                    extra_data["modified_charts"] = msg["modified_charts"]
                if msg.get("charts"):
                    extra_data["charts"] = msg["charts"]
                if msg.get("tables"):
                    extra_data["tables"] = msg["tables"]
                if msg.get("action_type"):
                    extra_data["action_type"] = msg["action_type"]
                if msg.get("quoted_text"):
                    extra_data["quoted_text"] = msg["quoted_text"]
                
                # 创建 DialogHistory 记录
                dialog_history = DialogHistory(
                    session_id=session.id,
                    role=role,
                    content=content,
                    extra_data=extra_data if extra_data else None,
                    created_at=created_at
                )
                db.add(dialog_history)
                migrated_count += 1
            
            # 提交当前会话的迁移
            db.commit()
            logger.info(f"会话 {session.id} 迁移完成")
        
        logger.info(f"迁移完成！共迁移 {migrated_count} 条消息，跳过 {skipped_count} 个会话")
        
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_dialog_history()
