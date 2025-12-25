#!/usr/bin/env python3
"""重置管理员密码"""
import os
import asyncio
from sqlalchemy import select

# 设置使用本地环境变量
os.environ["ENV_FILE"] = ".env.local"

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import pwd_context

async def reset_admin_password():
    """重置管理员密码"""
    print("=" * 60)
    print("重置管理员密码")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 查找 admin 用户
        result = db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        
        if admin:
            # 重置密码
            new_password = "admin123!"
            admin.password_hash = pwd_context.hash(new_password)
            db.commit()
            print(f"\n✓ 管理员密码已重置")
            print(f"  用户名: admin")
            print(f"  密码: {new_password}")
        else:
            # 创建新的管理员用户
            print("\n未找到 admin 用户，正在创建...")
            new_password = "admin123!"
            admin = User(
                username="admin",
                password_hash=pwd_context.hash(new_password),
                email="admin@example.com",
                full_name="系统管理员",
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print(f"\n✓ 管理员用户已创建")
            print(f"  用户名: admin")
            print(f"  密码: {new_password}")
            print(f"  邮箱: admin@example.com")
        
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
    asyncio.run(reset_admin_password())
