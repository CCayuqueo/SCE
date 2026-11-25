from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine

from app.core.config import Settings

metadata = MetaData()


def make_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
    )
