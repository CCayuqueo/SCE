"""esquema inicial SRC

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
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
        sa.CheckConstraint(
            "email = lower(btrim(email))", name="ck_users_email_normalized"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "rooms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("owner_role", sa.Text(), server_default="admin", nullable=False),
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
        sa.CheckConstraint("owner_role = 'admin'", name="ck_rooms_owner_role"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_rooms_code"),
    )
    op.create_index(
        op.f("ix_rooms_owner_user_id"), "rooms", ["owner_user_id"], unique=False
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("csrf_token_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_table(
        "room_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column(
            "joined_at",
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
        sa.CheckConstraint("role IN ('admin', 'member')", name="ck_room_members_role"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "room_id", "user_id", "role", name="uq_room_members_room_user_role"
        ),
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
    )
    op.create_index(
        op.f("ix_room_members_user_id"), "room_members", ["user_id"], unique=False
    )
    # La relación es circular: ambas tablas deben existir antes de añadirla.
    op.create_foreign_key(
        "fk_room_owner_membership",
        "rooms",
        "room_members",
        ["id", "owner_user_id", "owner_role"],
        ["room_id", "user_id", "role"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_table(
        "schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", sa.String(length=15), server_default="draft", nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
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
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft', 'confirmed')", name="ck_schedules_status"
        ),
        sa.CheckConstraint("version >= 1", name="ck_schedules_version"),
        sa.ForeignKeyConstraint(["member_id"], ["room_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", name="uq_schedules_member"),
    )
    op.create_table(
        "schedule_blocks",
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.SmallInteger(), nullable=False),
        sa.Column("block", sa.SmallInteger(), nullable=False),
        sa.Column("is_occupied", sa.Boolean(), nullable=False),
        sa.CheckConstraint("block BETWEEN 1 AND 10", name="ck_schedule_blocks_block"),
        sa.CheckConstraint("day BETWEEN 1 AND 7", name="ck_schedule_blocks_day"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("schedule_id", "day", "block"),
    )


def downgrade() -> None:
    op.drop_constraint("fk_room_owner_membership", "rooms", type_="foreignkey")
    op.drop_table("schedule_blocks")
    op.drop_table("schedules")
    op.drop_index(op.f("ix_room_members_user_id"), table_name="room_members")
    op.drop_table("room_members")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_rooms_owner_user_id"), table_name="rooms")
    op.drop_table("rooms")
    op.drop_table("users")
