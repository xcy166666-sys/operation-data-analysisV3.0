"""add dialog_histories table for AI conversation persistence

Revision ID: add_dialog_histories
Revises: add_session_versions
Create Date: 2025-12-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_dialog_histories"
down_revision = "add_session_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dialog_histories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),  # 'user' | 'assistant' | 'system'
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # 复合索引：按session_id和时间排序查询
    op.create_index(
        "ix_dialog_histories_session_created",
        "dialog_histories",
        ["session_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_dialog_histories_session_created", table_name="dialog_histories")
    op.drop_table("dialog_histories")
