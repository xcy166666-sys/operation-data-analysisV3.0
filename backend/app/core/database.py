"""
数据库连接和会话管理
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接前先ping，确保连接有效
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接超时时间
    pool_recycle=3600,  # 连接回收时间（1小时）
    echo=settings.DEBUG,  # 是否打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入:
    
    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有表（开发环境使用，生产环境使用Alembic迁移）
    """
    Base.metadata.create_all(bind=engine)

