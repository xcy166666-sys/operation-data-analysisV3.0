"""add_draft_status_to_batch_analysis

Revision ID: 2f7e224b9ce5
Revises: 77eb29d86bb3
Create Date: 2025-11-27 04:04:07.185753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f7e224b9ce5'
down_revision = '77eb29d86bb3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除旧的约束
    op.drop_constraint('batch_analysis_sessions_status_check', 'batch_analysis_sessions', type_='check')
    # 添加新的约束，包含draft状态
    op.create_check_constraint(
        'batch_analysis_sessions_status_check',
        'batch_analysis_sessions',
        "status IN ('draft', 'processing', 'completed', 'failed', 'partial_failed')"
    )


def downgrade() -> None:
    # 删除新约束
    op.drop_constraint('batch_analysis_sessions_status_check', 'batch_analysis_sessions', type_='check')
    # 恢复旧约束
    op.create_check_constraint(
        'batch_analysis_sessions_status_check',
        'batch_analysis_sessions',
        "status IN ('processing', 'completed', 'failed', 'partial_failed')"
    )

