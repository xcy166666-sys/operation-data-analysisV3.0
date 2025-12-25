#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理员权限
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User

def main():
    db: Session = SessionLocal()
    
    try:
        # 设置 admin 账号为管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            admin.is_admin = True
            db.commit()
            print("✅ admin 账号已设置为管理员")
            print(f"   用户名: admin")
            print(f"   is_admin: {admin.is_admin}")
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

