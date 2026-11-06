"""add card due month offset"""
from alembic import op
import sqlalchemy as sa


revision = "b6d42c9f71e2"
down_revision = "e0ad0c5cbcf7"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite supports a direct ADD COLUMN; avoid table recreation because cards
    # are referenced by purchases and may already contain financial history.
    op.add_column(
        "cards",
        sa.Column("due_month_offset", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade():
    op.drop_column("cards", "due_month_offset")
