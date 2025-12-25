"""
用户管理API（仅管理员可访问）
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListQuery
)
from app.schemas.common import SuccessResponse, PaginatedData, PaginationInfo
from app.models.user import User
from app.auth.dependencies import get_current_superadmin
from app.core.security import get_password_hash

router = APIRouter()


@router.get("", response_model=SuccessResponse[PaginatedData[UserResponse]])
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    获取用户列表（分页、搜索）
    
    仅管理员可访问
    """
    # 构建查询
    query = db.query(User)
    
    # 搜索过滤
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    # 排序：超级管理员（is_admin=True）永远排在第一位，其他用户按创建时间倒序
    from sqlalchemy import case
    users = query.order_by(
        case((User.is_admin == True, 0), else_=1),  # 超级管理员排第一
        User.created_at.desc()
    ).offset(offset).limit(page_size).all()
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return SuccessResponse(
        data=PaginatedData(
            items=[UserResponse.model_validate(user) for user in users],
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            )
        ),
        message="获取用户列表成功"
    )


@router.post("", response_model=SuccessResponse[UserResponse])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    创建新用户
    
    仅管理员可访问
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=True,
        is_admin=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SuccessResponse(
        data=UserResponse.model_validate(new_user),
        message="创建用户成功"
    )


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    更新用户信息
    
    仅管理员可访问
    - 只能更新邮箱和全名
    - 不能修改用户名
    """
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    db.commit()
    db.refresh(user)
    
    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="更新用户成功"
    )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    删除用户
    
    仅管理员可访问
    - 不能删除自己
    - 级联删除用户相关的所有数据
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除超级管理员
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除超级管理员"
        )
    
    # 删除用户（级联删除相关数据）
    db.delete(user)
    db.commit()
    
    return SuccessResponse(
        message="删除用户成功"
    )

