"""add sheet_index to workflow_binding

Revision ID: f3g4h5i6j7k8
Revises: e2f3g4h5i6j7
Create Date: 2025-01-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f3g4h5i6j7k8'
down_revision = 'e2f3g4h5i6j7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加sheet_index字段到workflow_bindings表
    op.add_column('workflow_bindings', sa.Column('sheet_index', sa.Integer(), nullable=True))
    
    # 创建索引
    op.create_index(
        'ix_workflow_bindings_function_key_sheet_index',
        'workflow_bindings',
        ['function_key', 'sheet_index'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_workflow_bindings_function_key_sheet_index', table_name='workflow_bindings')
    op.drop_column('workflow_bindings', 'sheet_index')

