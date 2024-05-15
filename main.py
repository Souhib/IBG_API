from contextlib import asynccontextmanager

import uvicorn
from aredis_om import Migrator
from fastapi import FastAPI

from ibg.app import create_app
from ibg.database import create_app_engine, create_db_and_tables
from ibg.logger_config import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    await Migrator().run()
    engine = create_app_engine()
    create_db_and_tables(engine)
    engine.dispose()
    yield


app = create_app(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
