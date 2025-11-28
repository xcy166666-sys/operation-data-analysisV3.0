"""
创建初始管理员用户脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def create_admin_user():
    """创建管理员用户"""
    db: Session = SessionLocal()
    
    try:
        # 检查是否已存在管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("管理员用户已存在，跳过创建")
            return
        
        # 创建管理员用户
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123456"),  # 默认密码，请修改
            full_name="系统管理员",
            email="admin@example.com",
            is_superadmin=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ 管理员用户创建成功")
        print(f"   用户名: admin")
        print(f"   密码: admin123456")
        print("   ⚠️  请登录后立即修改密码！")
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()

