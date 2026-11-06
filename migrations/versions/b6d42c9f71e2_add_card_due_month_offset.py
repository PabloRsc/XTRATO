"""add card due month offset"""
from alembic import op
import sqlalchemy as sa


revision = "b6d42c9f71e2"
down_revision = "e0ad0c5cbcf7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cards",
        sa.Column("due_month_offset", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint(
        "ck_card_due_month_offset",
        "cards",
        "due_month_offset IN (0, 1)",
    )


def downgrade():
    op.drop_constraint("ck_card_due_month_offset", "cards", type_="check")
    op.drop_column("cards", "due_month_offset")
