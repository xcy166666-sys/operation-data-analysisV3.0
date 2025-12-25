"""add function_modules table

Revision ID: e2f3g4h5i6j7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e2f3g4h5i6j7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建功能模块表
    op.create_table('function_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('function_key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('route_path', sa.String(length=200), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True, server_default='operation'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_function_modules_function_key'), 'function_modules', ['function_key'], unique=True)
    op.create_index(op.f('ix_function_modules_id'), 'function_modules', ['id'], unique=False)
    op.create_index(op.f('ix_function_modules_is_enabled'), 'function_modules', ['is_enabled'], unique=False)
    
    # 插入初始数据
    op.execute("""
        INSERT INTO function_modules (function_key, name, description, route_path, icon, category, is_enabled, sort_order, created_at, updated_at)
        VALUES
        ('operation_data_analysis', '单文件数据分析', '上传单个Excel文件，快速生成数据分析报告', '/operation', 'Document', 'operation', true, 1, NOW(), NOW()),
        ('operation_batch_analysis', '批量数据分析', '上传包含多个Sheet的Excel文件，批量生成分析报告', '/operation/batch', 'Files', 'operation', true, 2, NOW(), NOW()),
        ('custom_operation_data_analysis', '黄伟斌定制款数据分析工具', '定制化批量分析，支持根据Sheet索引自动选择工作流', '/operation/custom-batch', 'Setting', 'operation', true, 3, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_function_modules_is_enabled'), table_name='function_modules')
    op.drop_index(op.f('ix_function_modules_id'), table_name='function_modules')
    op.drop_index(op.f('ix_function_modules_function_key'), table_name='function_modules')
    op.drop_table('function_modules')

