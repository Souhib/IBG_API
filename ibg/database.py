from sqlalchemy import create_engine, Engine
from sqlalchemy.event import listens_for
from sqlmodel import SQLModel

from ibg.settings import Settings


def create_app_engine():
    settings = Settings()
    if "sqlite" in settings.database_url:
        engine = create_engine(
            settings.database_url, connect_args={"check_same_thread": False}, echo=True
        )

        @listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    else:
        engine = create_engine(settings.database_url, echo=True)
    SQLModel.metadata.create_all(engine)
    return engine


def create_db_and_tables(engine: Engine):
    SQLModel.metadata.create_all(engine)
