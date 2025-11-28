"""
Alembic环境配置（简化版，仅包含运营数据分析相关模型）
"""
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 导入Base和所有模型（简化版，仅包含运营数据分析相关模型）
from app.core.database import Base
from app.models.user import User
from app.models.session import AnalysisSession
from app.models.workflow import Workflow, WorkflowBinding
from app.models.batch_analysis import BatchAnalysisSession, SheetReport
from app.models.custom_batch_analysis import CustomBatchAnalysisSession, CustomSheetReport

# Alembic配置对象
config = context.config

# 从环境变量读取数据库URL
database_url = os.getenv("DATABASE_URL")
if database_url:
    # 使用原始字符串避免ConfigParser的插值语法问题
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

