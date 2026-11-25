from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.config import Settings
from app.core.database import make_engine
from app.models import Room, RoomMember, Schedule, ScheduleBlock, Session, User

pytestmark = pytest.mark.integration


@pytest.fixture
def db():
    engine = make_engine(Settings())
    try:
        with DbSession(engine) as session:
            yield session
    finally:
        engine.dispose()


def create_room(db):
    owner = User(
        name="Propietario", email=f"{uuid4()}@example.com", password_hash="test"
    )
    member = User(
        name="Integrante", email=f"{uuid4()}@example.com", password_hash="test"
    )
    db.add_all([owner, member])
    db.flush()
    room = Room(
        name="Sala de prueba", code=uuid4().hex[:12].upper(), owner_user_id=owner.id
    )
    db.add(room)
    db.flush()
    membership = RoomMember(room_id=room.id, user_id=owner.id, role="admin")
    candidate = RoomMember(room_id=room.id, user_id=member.id, role="member")
    db.add_all([membership, candidate])
    db.flush()
    return owner, room, membership, candidate


def test_room_requires_admin_membership_and_restricts_owner_deletion(db):
    owner, room, membership, _ = create_room(db)

    with (
        pytest.raises(IntegrityError, match="fk_room_owner_membership"),
        db.begin_nested(),
    ):
        membership.role = "member"
        db.flush()
        db.execute(text("SET CONSTRAINTS fk_room_owner_membership IMMEDIATE"))

    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(delete(User).where(User.id == owner.id))

    db.execute(text("SET CONSTRAINTS fk_room_owner_membership IMMEDIATE"))
    assert room.owner_user_id == owner.id
    assert membership.role == "admin"


def test_ownership_transfer_preserves_room_and_cascades_account_data(db):
    owner, room, membership, candidate = create_room(db)
    schedule = Schedule(member_id=membership.id)
    db.add(schedule)
    db.flush()
    db.add(ScheduleBlock(schedule_id=schedule.id, day=7, block=10, is_occupied=True))
    db.add(
        Session(
            user_id=owner.id,
            token_hash=uuid4().hex,
            csrf_token_hash="test",
            expires_at=datetime.now(UTC),
        )
    )
    db.flush()

    owner_id, membership_id, schedule_id = owner.id, membership.id, schedule.id
    candidate.role = "admin"
    room.owner_user_id = candidate.user_id
    db.flush()
    db.execute(delete(User).where(User.id == owner_id))
    db.execute(text("SET CONSTRAINTS fk_room_owner_membership IMMEDIATE"))

    assert (
        db.scalar(select(Room.owner_user_id).where(Room.id == room.id))
        == candidate.user_id
    )
    assert (
        db.scalar(select(RoomMember.id).where(RoomMember.id == membership_id)) is None
    )
    assert db.scalar(select(Schedule.id).where(Schedule.id == schedule_id)) is None
    assert (
        db.scalar(
            select(ScheduleBlock.day).where(ScheduleBlock.schedule_id == schedule_id)
        )
        is None
    )
    assert db.scalar(select(Session.id).where(Session.user_id == owner_id)) is None


def test_email_membership_and_schedule_coordinates_are_constrained(db):
    owner, room, membership, _ = create_room(db)
    schedule = Schedule(member_id=membership.id)
    db.add(schedule)
    db.flush()
    block = {"schedule_id": schedule.id, "day": 1, "block": 1, "is_occupied": False}
    db.execute(insert(ScheduleBlock).values(**block))

    invalid_rows = [
        (
            User,
            {"name": "Duplicado", "email": owner.email, "password_hash": "test"},
            "uq_users_email",
        ),
        (
            User,
            {
                "name": "Inválido",
                "email": " MAIL@EXAMPLE.COM ",
                "password_hash": "test",
            },
            "ck_users_email_normalized",
        ),
        (
            RoomMember,
            {"room_id": room.id, "user_id": owner.id, "role": "member"},
            "uq_room_members_room_user",
        ),
        (Schedule, {"member_id": membership.id}, "uq_schedules_member"),
        (ScheduleBlock, block, "schedule_blocks_pkey"),
        (ScheduleBlock, {**block, "day": 8}, "ck_schedule_blocks_day"),
        (ScheduleBlock, {**block, "block": 11}, "ck_schedule_blocks_block"),
    ]
    for model, values, constraint in invalid_rows:
        with pytest.raises(IntegrityError, match=constraint), db.begin_nested():
            db.execute(insert(model).values(**values))
