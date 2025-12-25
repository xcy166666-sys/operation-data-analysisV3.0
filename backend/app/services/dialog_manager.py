"""
对话历史管理器
负责存储和检索对话历史记录
支持内存存储和数据库持久化两种模式
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session

from app.models.dialog_history import DialogHistory


class DialogManager:
    """对话历史管理器"""

    def __init__(self):
        # 内存存储对话历史，格式: {session_id: [messages]}
        self._dialog_history: Dict[str, List[Dict[str, Any]]] = {}
        # 会话状态，格式: {session_id: {conversation_id, file_id, last_activity}}
        self._session_states: Dict[str, Dict[str, Any]] = {}

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        modified_charts: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        保存对话消息

        Args:
            session_id: 会话ID
            role: 消息角色 ("user" | "assistant")
            content: 消息内容
            modified_charts: 修改后的图表配置（可选）
        """

        message = {
            "id": f"{session_id}_{int(datetime.now().timestamp() * 1000)}",
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "modified_charts": modified_charts
        }

        if session_id not in self._dialog_history:
            self._dialog_history[session_id] = []

        self._dialog_history[session_id].append(message)

        # 更新会话状态
        self._update_session_state(session_id)

        logger.debug(f"[DialogManager] 保存消息: session_id={session_id}, role={role}, content_length={len(content)}")

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            session_id: 会话ID
            limit: 最大返回消息数量

        Returns:
            对话历史消息列表
        """

        if session_id not in self._dialog_history:
            return []

        messages = self._dialog_history[session_id]
        return messages[-limit:] if limit > 0 else messages

    async def save_session_state(
        self,
        session_id: str,
        conversation_id: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> None:
        """
        保存会话状态

        Args:
            session_id: 会话ID
            conversation_id: 阿里百炼对话ID
            file_id: 文件ID
        """

        if session_id not in self._session_states:
            self._session_states[session_id] = {}

        state = self._session_states[session_id]
        if conversation_id:
            state["conversation_id"] = conversation_id
        if file_id:
            state["file_id"] = file_id
        state["last_activity"] = datetime.now().isoformat()

        logger.debug(f"[DialogManager] 保存会话状态: session_id={session_id}, conversation_id={conversation_id}")

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话状态

        Args:
            session_id: 会话ID

        Returns:
            会话状态信息
        """

        return self._session_states.get(session_id)

    async def clear_session_history(self, session_id: str) -> None:
        """
        清除会话历史

        Args:
            session_id: 会话ID
        """

        if session_id in self._dialog_history:
            del self._dialog_history[session_id]

        if session_id in self._session_states:
            del self._session_states[session_id]

        logger.info(f"[DialogManager] 清除会话历史: session_id={session_id}")

    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        清理过期会话

        Args:
            max_age_hours: 最大会话年龄（小时）

        Returns:
            清理的会话数量
        """

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_sessions = []

        for session_id, state in self._session_states.items():
            last_activity = state.get("last_activity")
            if last_activity:
                try:
                    last_activity_time = datetime.fromisoformat(last_activity)
                    if last_activity_time < cutoff_time:
                        expired_sessions.append(session_id)
                except:
                    # 解析时间失败，认为是过期
                    expired_sessions.append(session_id)

        # 清理过期会话
        for session_id in expired_sessions:
            await self.clear_session_history(session_id)

        logger.info(f"[DialogManager] 清理过期会话: {len(expired_sessions)} 个")
        return len(expired_sessions)

    def _update_session_state(self, session_id: str) -> None:
        """更新会话状态的最后活动时间"""

        if session_id not in self._session_states:
            self._session_states[session_id] = {}

        self._session_states[session_id]["last_activity"] = datetime.now().isoformat()

    # 导出/导入功能（用于调试和备份）

    def export_dialog_history(self, session_id: str) -> str:
        """导出对话历史为JSON字符串"""

        history = self._dialog_history.get(session_id, [])
        state = self._session_states.get(session_id, {})

        data = {
            "session_id": session_id,
            "state": state,
            "messages": history,
            "exported_at": datetime.now().isoformat()
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_dialog_history(self, json_data: str) -> bool:
        """从JSON字符串导入对话历史"""

        try:
            data = json.loads(json_data)
            session_id = data["session_id"]

            self._dialog_history[session_id] = data.get("messages", [])
            self._session_states[session_id] = data.get("state", {})

            logger.info(f"[DialogManager] 导入对话历史成功: session_id={session_id}")
            return True

        except Exception as e:
            logger.error(f"[DialogManager] 导入对话历史失败: {str(e)}")
            return False

    # 统计功能

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""

        total_sessions = len(self._dialog_history)
        total_messages = sum(len(messages) for messages in self._dialog_history.values())

        active_sessions = 0
        for state in self._session_states.values():
            if state.get("conversation_id"):
                active_sessions += 1

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "memory_usage": self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> str:
        """估算内存使用量"""

        # 粗略估算
        history_size = len(json.dumps(self._dialog_history, default=str))
        state_size = len(json.dumps(self._session_states, default=str))
        total_bytes = history_size + state_size

        # 转换为可读格式
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        else:
            return f"{total_bytes / (1024 * 1024):.1f} MB"

    # ==================== 数据库持久化方法 ====================

    def save_message_to_db(
        self,
        db: Session,
        session_id: int,
        role: str,
        content: str,
        extra_data: Optional[Dict[str, Any]] = None,
        version_id: Optional[int] = None
    ) -> DialogHistory:
        """
        保存消息到数据库

        Args:
            db: 数据库会话
            session_id: 分析会话ID
            role: 消息角色 ("user" | "assistant")
            content: 消息内容
            extra_data: 额外数据（action_type, modified_charts等）
            version_id: 版本ID（用于标记此消息属于哪个版本）

        Returns:
            保存的DialogHistory对象
        """
        history = DialogHistory(
            session_id=session_id,
            role=role,
            content=content,
            extra_data=extra_data,
            version_id=version_id
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        logger.debug(f"[DialogManager] 保存消息到数据库: session_id={session_id}, role={role}, version_id={version_id}")
        return history

    def get_conversation_history_from_db(
        self,
        db: Session,
        session_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        从数据库获取对话历史

        Args:
            db: 数据库会话
            session_id: 分析会话ID
            limit: 最大返回消息数量

        Returns:
            对话历史消息列表（按时间正序）
        """
        histories = db.query(DialogHistory)\
            .filter(DialogHistory.session_id == session_id)\
            .order_by(DialogHistory.created_at.desc())\
            .limit(limit)\
            .all()

        # 反转为正序（从旧到新）
        return [h.to_dict() for h in reversed(histories)]

    def get_messages_for_ai(
        self,
        db: Session,
        session_id: int,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """
        获取用于AI上下文的消息列表

        Args:
            db: 数据库会话
            session_id: 分析会话ID
            limit: 最大消息数量

        Returns:
            格式化的消息列表，用于传递给AI模型
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        histories = self.get_conversation_history_from_db(db, session_id, limit)

        messages = []
        for h in histories:
            messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        return messages

    def clear_session_history_from_db(
        self,
        db: Session,
        session_id: int
    ) -> int:
        """
        清除数据库中的会话历史

        Args:
            db: 数据库会话
            session_id: 分析会话ID

        Returns:
            删除的消息数量
        """
        count = db.query(DialogHistory)\
            .filter(DialogHistory.session_id == session_id)\
            .delete()
        db.commit()

        logger.info(f"[DialogManager] 清除数据库会话历史: session_id={session_id}, count={count}")
        return count

    def get_dialog_count_from_db(
        self,
        db: Session,
        session_id: int
    ) -> int:
        """
        获取会话的对话消息数量

        Args:
            db: 数据库会话
            session_id: 分析会话ID

        Returns:
            消息数量
        """
        return db.query(DialogHistory)\
            .filter(DialogHistory.session_id == session_id)\
            .count()










