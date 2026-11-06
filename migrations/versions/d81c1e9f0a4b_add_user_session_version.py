"""add user session version"""
from alembic import op
import sqlalchemy as sa


revision = "d81c1e9f0a4b"
down_revision = "b6d42c9f71e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("session_version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("users", "session_version")
