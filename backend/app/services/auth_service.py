"""
认证服务（简化版，移除项目依赖）
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_session_token, create_api_token
from app.core.redis import RedisClient
from app.core.config import settings
from app.models.user import User


class AuthService:
    """认证服务类"""
    
    @staticmethod
    async def authenticate_user(
        db: Session,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回User对象，失败返回None
        """
        # 查询用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None
        
        # 检查用户状态
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def create_session(
        redis: RedisClient,
        user: User
    ) -> Tuple[str, str]:
        """
        创建用户会话（简化版，移除project_id）
        
        Args:
            redis: Redis客户端
            user: 用户对象
            
        Returns:
            (session_id, session_token)
        """
        # 生成Session ID
        session_id = str(uuid.uuid4())
        
        # 生成Session Token（使用固定project_id=1）
        session_token = create_session_token(user.id, project_id=1)
        
        # 存储Session数据到Redis
        session_data = {
            "user_id": user.id,
            "username": user.username,
            "project_id": 1,  # 固定项目ID
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 设置过期时间（小时转秒）
        expire_seconds = settings.SESSION_EXPIRE_HOURS * 3600
        await redis.set_json(
            f"session:{session_id}",
            session_data,
            expire=expire_seconds
        )
        
        return session_id, session_token
    
    @staticmethod
    async def destroy_session(
        redis: RedisClient,
        session_id: str
    ) -> bool:
        """
        销毁用户会话
        
        Args:
            redis: Redis客户端
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        await redis.delete(f"session:{session_id}")
        return True
    
    @staticmethod
    async def update_last_login(
        db: Session,
        user: User
    ) -> None:
        """
        更新用户最后登录时间
        
        Args:
            db: 数据库会话
            user: 用户对象
        """
        user.last_login_at = datetime.utcnow()
        db.commit()
    
    @staticmethod
    def generate_api_token(
        user_id: int,
        purpose: str = "api"
    ) -> str:
        """
        生成API访问令牌（简化版，移除project_id）
        
        Args:
            user_id: 用户ID
            purpose: 用途标识
            
        Returns:
            API令牌
        """
        return create_api_token(user_id, project_id=1, purpose=purpose)

