"""
认证依赖项（用于FastAPI Depends）- 简化版，移除项目依赖
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Cookie
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.redis import get_redis, RedisClient
from app.models.user import User
from app.schemas.auth import TokenData


async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    从Authorization Header获取当前用户（JWT Token）
    用于API访问
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解析Token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证方式错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解码Token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token数据不完整",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


async def get_current_user_from_session(
    auth_session_id: Optional[str] = Cookie(None, alias="session_id"),
    redis: RedisClient = Depends(get_redis),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    从Session Cookie获取当前用户
    用于Web浏览器访问
    """
    if not auth_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
        )

    # 从Redis获取Session数据
    session_data = await redis.get_json(f"session:{auth_session_id}")
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期，请重新登录",
        )
    
    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话数据不完整",
        )
    
    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_session_id: Optional[str] = Cookie(None, alias="session_id"),
    redis: RedisClient = Depends(get_redis),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户（支持Token和Session两种方式）
    优先使用Token，其次使用Session
    """
    # 尝试Token认证
    if authorization:
        try:
            return await get_current_user_from_token(authorization, db)
        except HTTPException:
            pass

    # 尝试Session认证
    if auth_session_id:
        try:
            return await get_current_user_from_session(auth_session_id, redis, db)
        except HTTPException:
            pass
    
    # 都失败
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或认证信息无效",
    )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


def get_current_superadmin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前超级管理员"""
    if not current_user.is_admin:  # 使用is_admin字段
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user

