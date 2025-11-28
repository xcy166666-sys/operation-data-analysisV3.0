"""
安全相关配置和工具（运营数据分析独立版）
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    Args:
        password: 明文密码
    
    Returns:
        哈希密码
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据（通常包含user_id等）
        expires_delta: 过期时间增量，None则使用配置中的默认值
    
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的数据，如果无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_session_token(user_id: int, project_id: int = 1) -> str:
    """
    创建Session令牌（用于浏览器访问）
    
    Args:
        user_id: 用户ID
        project_id: 项目ID（固定为1，简化版）
    
    Returns:
        Session令牌
    """
    data = {
        "user_id": user_id,
        "project_id": project_id,
        "type": "session"
    }
    return create_access_token(
        data,
        expires_delta=timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    )


def create_api_token(
    user_id: int,
    project_id: int = 1,
    purpose: str = "api"
) -> str:
    """
    创建API令牌（用于API访问）
    
    Args:
        user_id: 用户ID
        project_id: 项目ID（固定为1，简化版）
        purpose: 用途标识
    
    Returns:
        API令牌
    """
    data = {
        "user_id": user_id,
        "project_id": project_id,
        "type": "api",
        "purpose": purpose
    }
    return create_access_token(data)

