import os

from aredis_om import get_redis_connection
from sqlalchemy import Engine, create_engine
from sqlalchemy.event import listens_for
from sqlmodel import SQLModel

from ibg.settings import Settings


def create_app_engine():
    settings = Settings()
    if "sqlite" in settings.database_url:
        engine = create_engine(settings.database_url, connect_args={"check_same_thread": False}, echo=True)

        @listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # SQLAlchemyInstrumentor().instrument(engine=engine)

    else:
        engine = create_engine(settings.database_url, echo=True)
    return engine


def create_db_and_tables(engine: Engine):
    SQLModel.metadata.create_all(engine)


def get_redis_om_connection():
    redis_url = os.getenv("REDIS_OM_URL")
    host, port = redis_url.split("//")[1].split(":")
    return get_redis_connection(host=host, port=int(port), decode_responses=True, encoding="utf-8")
