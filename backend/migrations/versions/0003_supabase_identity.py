"""Allow profiles whose credentials and email are managed by Supabase."""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", nullable=True)
    op.alter_column("users", "email", nullable=True)
    op.create_check_constraint(
        "ck_users_credentials_pair",
        "users",
        "(email IS NULL) = (password_hash IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_credentials_pair", "users", type_="check")
    op.alter_column("users", "email", nullable=False)
    op.alter_column("users", "password_hash", nullable=False)
