"""add_custom_batch_analysis_tables

Revision ID: a1b2c3d4e5f6
Revises: 2f7e224b9ce5
Create Date: 2025-11-27 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2f7e224b9ce5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建定制化批量分析会话表
    op.create_table(
        'custom_batch_analysis_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=False),
        sa.Column('original_file_path', sa.String(length=500), nullable=False),
        sa.Column('split_files_dir', sa.String(length=500), nullable=False),
        sa.Column('sheet_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('draft', 'processing', 'completed', 'failed', 'partial_failed')", name='custom_batch_analysis_sessions_status_check')
    )
    op.create_index(op.f('ix_custom_batch_analysis_sessions_id'), 'custom_batch_analysis_sessions', ['id'], unique=False)
    
    # 创建定制化Sheet报告表
    op.create_table(
        'custom_sheet_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('custom_batch_session_id', sa.Integer(), nullable=False),
        sa.Column('sheet_name', sa.String(length=255), nullable=False),
        sa.Column('sheet_index', sa.Integer(), nullable=False),
        sa.Column('split_file_path', sa.String(length=500), nullable=False),
        sa.Column('report_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_status', sa.String(length=50), nullable=False),
        sa.Column('dify_conversation_id', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['custom_batch_session_id'], ['custom_batch_analysis_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("report_status IN ('pending', 'generating', 'completed', 'failed')", name='custom_sheet_reports_status_check')
    )
    op.create_index(op.f('ix_custom_sheet_reports_id'), 'custom_sheet_reports', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_custom_sheet_reports_id'), table_name='custom_sheet_reports')
    op.drop_table('custom_sheet_reports')
    op.drop_index(op.f('ix_custom_batch_analysis_sessions_id'), table_name='custom_batch_analysis_sessions')
    op.drop_table('custom_batch_analysis_sessions')

