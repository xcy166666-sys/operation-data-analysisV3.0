#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123456"),
            full_name="System Admin",
            email="admin@example.com",
            is_admin=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123456")
        print("Please change password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

