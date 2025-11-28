"""
认证相关API（简化版，移除项目依赖）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_redis
from app.core.redis import RedisClient
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, ChangePasswordRequest, RegisterRequest
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService
from app.auth.dependencies import get_current_active_user
from app.core.security import get_password_hash, verify_password
from app.models.user import User


router = APIRouter()


@router.post("/login", response_model=SuccessResponse[LoginResponse])
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """
    用户登录
    
    - 验证用户名和密码
    - 创建Session
    - 返回用户信息和Token
    """
    # 验证用户
    user = await AuthService.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建Session
    session_id, session_token = await AuthService.create_session(redis, user)
    
    # 更新最后登录时间
    await AuthService.update_last_login(db, user)
    
    # 设置Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600 * 24 * 7,  # 7天
        samesite="lax"
    )
    
    # 返回响应
    return SuccessResponse(
        data=LoginResponse(
            user={
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "is_superadmin": user.is_admin,  # 使用is_admin字段
                "is_admin": user.is_admin,  # 同时返回is_admin字段
                "is_active": user.is_active
            },
            token=session_token,
            session_id=session_id
        ),
        message="登录成功"
    )


@router.post("/register", response_model=SuccessResponse[LoginResponse])
async def register(
    register_data: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """
    用户注册
    
    - 创建新用户（普通用户，非管理员）
    - 自动登录
    - 创建Session
    - 返回用户信息和Token
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == register_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户（普通用户）
    new_user = User(
        username=register_data.username,
        password_hash=get_password_hash(register_data.password),
        email=register_data.email,
        full_name=register_data.full_name,
        is_active=True,
        is_admin=False  # 注册的用户都是普通用户
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 创建Session（自动登录）
    session_id, session_token = await AuthService.create_session(redis, new_user)
    
    # 设置Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600 * 24 * 7,  # 7天
        samesite="lax"
    )
    
    # 返回响应
    return SuccessResponse(
        data=LoginResponse(
            user={
                "id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "is_superadmin": False,
                "is_admin": False,
                "is_active": new_user.is_active
            },
            token=session_token,
            session_id=session_id
        ),
        message="注册成功"
    )


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str = None,
    redis: RedisClient = Depends(get_redis)
):
    """
    用户登出
    
    - 销毁Session
    - 清除Cookie
    """
    if session_id:
        await AuthService.destroy_session(redis, session_id)
    
    # 清除Cookie
    response.delete_cookie(key="session_id")
    
    return SuccessResponse(message="登出成功")


@router.get("/me", response_model=SuccessResponse[UserInfo])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    
    - 返回用户基本信息
    """
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        is_superadmin=current_user.is_admin,  # 使用is_admin字段
        is_active=current_user.is_active,
        current_project=None,  # 单项目系统，不需要项目信息
        permissions=[]  # 简化版，不实现权限系统
    )
    
    return SuccessResponse(data=user_info)


@router.put("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    - 验证旧密码
    - 更新为新密码
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return SuccessResponse(message="密码修改成功")


@router.get("/verify-session")
async def verify_session(
    current_user: User = Depends(get_current_active_user)
):
    """
    验证Session是否有效
    
    用于Nginx auth_request指令
    返回200表示验证通过，401表示未登录
    """
    return Response(status_code=status.HTTP_200_OK)

