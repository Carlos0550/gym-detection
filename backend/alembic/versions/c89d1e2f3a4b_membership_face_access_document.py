"""membership face_embeddings access_logs document biometric_consent

Revision ID: c89d1e2f3a4b
Revises: b67c2a3d4e5f
Create Date: 2026-06-14 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


revision: str = "c89d1e2f3a4b"
down_revision: str | Sequence[str] | None = "b67c2a3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        "DO $$ BEGIN "
        "    CREATE TYPE membership_status AS ENUM "
        "('ACTIVE', 'EXPIRED', 'CANCELLED', 'SUSPENDED'); "
        "EXCEPTION "
        "    WHEN duplicate_object THEN NULL; "
        "END $$"
    )
    op.execute(
        "DO $$ BEGIN "
        "    CREATE TYPE access_result AS ENUM "
        "('GRANTED', 'DENIED', 'UNKNOWN', 'LOW_CONFIDENCE'); "
        "EXCEPTION "
        "    WHEN duplicate_object THEN NULL; "
        "END $$"
    )

    op.add_column(
        "gym_users",
        sa.Column("biometric_consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("gym_users", sa.Column("document", sa.String(length=50), nullable=True))
    op.create_index(op.f("ix_gym_users_document"), "gym_users", ["document"], unique=False)
    op.create_unique_constraint(
        "uq_gym_user_document", "gym_users", ["gym_id", "document"]
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gym_user_id", sa.UUID(), nullable=False),
        sa.Column("gym_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ACTIVE",
                "EXPIRED",
                "CANCELLED",
                "SUSPENDED",
                name="membership_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gym_user_id"], ["gym_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memberships_gym_id"), "memberships", ["gym_id"], unique=False)
    op.create_index(
        op.f("ix_memberships_gym_user_id"), "memberships", ["gym_user_id"], unique=False
    )
    op.create_index(op.f("ix_memberships_user_id"), "memberships", ["user_id"], unique=False)

    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gym_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("embedding", Vector(512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_face_embeddings_gym_id"), "face_embeddings", ["gym_id"], unique=False
    )
    op.create_index(
        op.f("ix_face_embeddings_user_id"), "face_embeddings", ["user_id"], unique=False
    )

    op.create_table(
        "access_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gym_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "result",
            postgresql.ENUM(
                "GRANTED",
                "DENIED",
                "UNKNOWN",
                "LOW_CONFIDENCE",
                name="access_result",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("membership_status", sa.String(length=50), nullable=True),
        sa.Column("detail", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_logs_gym_id"), "access_logs", ["gym_id"], unique=False)
    op.create_index(
        op.f("ix_access_logs_created_at"), "access_logs", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_access_logs_user_id"), "access_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_access_logs_user_id"), table_name="access_logs")
    op.drop_index(op.f("ix_access_logs_created_at"), table_name="access_logs")
    op.drop_index(op.f("ix_access_logs_gym_id"), table_name="access_logs")
    op.drop_table("access_logs")

    op.drop_index(op.f("ix_face_embeddings_user_id"), table_name="face_embeddings")
    op.drop_index(op.f("ix_face_embeddings_gym_id"), table_name="face_embeddings")
    op.drop_table("face_embeddings")

    op.drop_index(op.f("ix_memberships_user_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_gym_user_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_gym_id"), table_name="memberships")
    op.drop_table("memberships")

    op.drop_constraint("uq_gym_user_document", "gym_users", type_="unique")
    op.drop_index(op.f("ix_gym_users_document"), table_name="gym_users")
    op.drop_column("gym_users", "document")
    op.drop_column("gym_users", "biometric_consent_at")

    op.execute("DROP TYPE IF EXISTS access_result")
    op.execute("DROP TYPE IF EXISTS membership_status")
