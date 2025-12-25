"""add version_id to dialog_history

Revision ID: 20251224_145706
Revises: 
Create Date: 2025-12-24 14:57:06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251224_145706'
down_revision = None  # 请根据实际情况修改为上一个版本的revision ID
branch_labels = None
depends_on = None


def upgrade():
    # 添加 version_id 列到 dialog_histories 表
    op.add_column('dialog_histories', 
        sa.Column('version_id', sa.Integer(), nullable=True)
    )
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_dialog_histories_version_id',
        'dialog_histories', 
        'analysis_session_versions',
        ['version_id'], 
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_dialog_histories_version_id', 'dialog_histories', type_='foreignkey')
    
    # 删除 version_id 列
    op.drop_column('dialog_histories', 'version_id')
