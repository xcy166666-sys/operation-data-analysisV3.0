#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新管理员密码
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
        # 更新 admin 账号密码
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            admin.password_hash = get_password_hash("admin123456")
            db.commit()
            print("✅ admin 账号密码已更新")
            print(f"   用户名: admin")
            print(f"   密码: admin123456")
        else:
            print("❌ admin 账号不存在")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()


