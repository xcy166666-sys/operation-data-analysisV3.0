#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建或更新管理员账号 admin7
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def main():
    db: Session = SessionLocal()
    
    try:
        # 检查是否已存在 admin7 账号
        admin7 = db.query(User).filter(User.username == "admin7").first()
        
        if admin7:
            # 如果存在，更新密码和管理员权限
            admin7.password_hash = get_password_hash("admin123456")
            admin7.is_admin = True
            admin7.is_active = True
            db.commit()
            print("✅ 管理员账号 admin7 已更新")
            print(f"   用户名: admin7")
            print(f"   密码: admin123456")
        else:
            # 如果不存在，创建新账号
            admin7 = User(
                username="admin7",
                password_hash=get_password_hash("admin123456"),
                full_name="系统管理员",
                email="admin7@example.com",
                is_admin=True,
                is_active=True
            )
            
            db.add(admin7)
            db.commit()
            print("✅ 管理员账号 admin7 创建成功")
            print(f"   用户名: admin7")
            print(f"   密码: admin123456")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

