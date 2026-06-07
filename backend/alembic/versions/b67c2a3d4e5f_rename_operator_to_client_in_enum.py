"""rename OPERATOR to CLIENT in gym_user_role enum

Revision ID: b67c2a3d4e5f
Revises: a42b5bb90a8f
Create Date: 2026-06-07 03:30:00.000000

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b67c2a3d4e5f"
down_revision: str | Sequence[str] | None = "a42b5bb90a8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE gym_user_role RENAME VALUE 'OPERATOR' TO 'CLIENT'")


def downgrade() -> None:
    op.execute("ALTER TYPE gym_user_role RENAME VALUE 'CLIENT' TO 'OPERATOR'")
