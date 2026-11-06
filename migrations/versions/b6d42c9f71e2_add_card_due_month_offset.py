"""add card due month offset"""
from alembic import op
import sqlalchemy as sa


revision = "b6d42c9f71e2"
down_revision = "e0ad0c5cbcf7"
branch_labels = None
depends_on = None


def upgrade():
    # Batch mode keeps this migration compatible with SQLite development databases.
    with op.batch_alter_table("cards") as batch_op:
        batch_op.add_column(
            sa.Column("due_month_offset", sa.Integer(), server_default="1", nullable=False),
        )
        batch_op.create_check_constraint(
            "ck_card_due_month_offset",
            "due_month_offset IN (0, 1)",
        )


def downgrade():
    with op.batch_alter_table("cards") as batch_op:
        batch_op.drop_constraint("ck_card_due_month_offset", type_="check")
        batch_op.drop_column("due_month_offset")
