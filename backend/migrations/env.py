from alembic import context

from app.core.config import Settings
from app.core.database import make_engine, metadata


def run_migrations() -> None:
    settings = Settings()
    if context.is_offline_mode():
        context.configure(
            url=settings.database_url.get_secret_value(),
            target_metadata=metadata,
            literal_binds=True,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = make_engine(settings)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
