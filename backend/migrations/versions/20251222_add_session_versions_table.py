"""add analysis_session_versions table

Revision ID: add_session_versions
Revises: d1bb7b20fe56
Create Date: 2025-12-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_session_versions"
down_revision = "f3g4h5i6j7k8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analysis_session_versions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("report_text", sa.Text(), nullable=True),
        sa.Column("report_html_charts", sa.Text(), nullable=True),
        sa.Column("report_charts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "idx_session_versions_session_id_version_no",
        "analysis_session_versions",
        ["session_id", "version_no"],
    )


def downgrade():
    op.drop_index("idx_session_versions_session_id_version_no", table_name="analysis_session_versions")
    op.drop_table("analysis_session_versions")

