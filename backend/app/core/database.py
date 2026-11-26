from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine

from app.core.config import Settings

metadata = MetaData()


def make_engine(settings: Settings) -> Engine:
    connection = {"connect_timeout": 3}
    if settings.supabase_url:
        # El timeout de consultas del pooler se configura en el rol src_app.
        connection["gssencmode"] = "disable"
    else:
        connection["options"] = "-c statement_timeout=3000"
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args=connection,
    )
