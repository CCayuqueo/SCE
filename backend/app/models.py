"""Esquema base de SRC. Las reglas entre filas se aplican en los servicios."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.database import metadata


class Base(DeclarativeBase):
    metadata = metadata


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "email = lower(btrim(email))", name="ck_users_email_normalized"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(100))
    email: Mapped[str] = mapped_column(sa.String(254))
    password_hash: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_rooms_code"),
        sa.CheckConstraint("owner_role = 'admin'", name="ck_rooms_owner_role"),
        sa.ForeignKeyConstraint(
            ["id", "owner_user_id", "owner_role"],
            ["room_members.room_id", "room_members.user_id", "room_members.role"],
            name="fk_room_owner_membership",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(sa.String(100))
    description: Mapped[str | None] = mapped_column(sa.String(500))
    code: Mapped[str] = mapped_column(sa.String(12))
    owner_user_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    owner_role: Mapped[str] = mapped_column(sa.Text, server_default="admin")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )


class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
        sa.UniqueConstraint(
            "room_id", "user_id", "role", name="uq_room_members_room_user_role"
        ),
        sa.CheckConstraint("role IN ('admin', 'member')", name="ck_room_members_role"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(sa.ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(sa.String(10))
    joined_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        sa.UniqueConstraint("member_id", name="uq_schedules_member"),
        sa.CheckConstraint(
            "status IN ('draft', 'confirmed')", name="ck_schedules_status"
        ),
        sa.CheckConstraint("version >= 1", name="ck_schedules_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("room_members.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(sa.String(15), server_default="draft")
    version: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    __table_args__ = (
        sa.CheckConstraint("day BETWEEN 1 AND 7", name="ck_schedule_blocks_day"),
        sa.CheckConstraint("block BETWEEN 1 AND 10", name="ck_schedule_blocks_block"),
    )

    schedule_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("schedules.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True)
    block: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True)
    is_occupied: Mapped[bool]


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(sa.Text)
    csrf_token_hash: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
