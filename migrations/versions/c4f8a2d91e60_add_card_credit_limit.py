"""add credit limit to cards"""
from alembic import op
import sqlalchemy as sa

revision = "c4f8a2d91e60"
down_revision = "b6d42c9f71e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cards", sa.Column("limit_cents", sa.BigInteger(), server_default="0", nullable=False))


def downgrade():
    op.drop_column("cards", "limit_cents")
