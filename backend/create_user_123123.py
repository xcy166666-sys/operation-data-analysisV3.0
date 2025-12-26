#!/usr/bin/env python3
"""创建或重置用户 123123"""
import os
import asyncio
from sqlalchemy import select

# 设置使用本地环境变量
os.environ["ENV_FILE"] = ".env.local"

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import pwd_context

async def create_or_reset_user():
    """创建或重置用户 123123"""
    print("=" * 60)
    print("创建/重置用户 123123")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 查找用户
        result = db.execute(select(User).where(User.username == "123123"))
        user = result.scalar_one_or_none()
        
        if user:
            # 重置密码
            new_password = "123123"
            user.password_hash = pwd_context.hash(new_password)
            db.commit()
            print(f"\n✓ 用户密码已重置")
            print(f"  用户名: 123123")
            print(f"  密码: {new_password}")
            print(f"  邮箱: {user.email}")
            print(f"  是否管理员: {user.is_admin}")
        else:
            # 创建新用户
            print("\n未找到用户 123123，正在创建...")
            new_password = "123123"
            user = User(
                username="123123",
                password_hash=pwd_context.hash(new_password),
                email="123123@example.com",
                full_name="用户123123",
                is_active=True,
                is_admin=False  # 普通用户
            )
            db.add(user)
            db.commit()
            print(f"\n✓ 用户已创建")
            print(f"  用户名: 123123")
            print(f"  密码: {new_password}")
            print(f"  邮箱: 123123@example.com")
            print(f"  是否管理员: False")
        
        print("\n" + "=" * 60)
        print("完成！现在可以使用上述账号登录系统")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_or_reset_user())
