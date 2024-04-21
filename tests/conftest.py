import pytest
from faker import Faker
from fastapi import FastAPI
from sqlalchemy import create_engine, Engine
from sqlalchemy.event import listens_for
from sqlalchemy.exc import NoResultFound
from sqlmodel import SQLModel, Session
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from ibg.controllers.game import GameController
from ibg.controllers.room import RoomController
from ibg.controllers.undercover import UndercoverController
from ibg.controllers.user import UserController
from ibg.models.errors import BaseError


@pytest.fixture(name="faker")
def get_faker() -> Faker:
    return Faker("fr_FR")


@pytest.fixture(name="engine")
def generate_test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def generate_test_db_session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture(name="user_controller")
def get_user_controller(session: Session) -> UserController:
    return UserController(session)


@pytest.fixture(name="undercover_controller")
def get_undercover_controller(session: Session) -> UndercoverController:
    return UndercoverController(session)


@pytest.fixture(name="game_controller")
def get_game_controller(session: Session) -> GameController:
    return GameController(session)


@pytest.fixture(name="room_controller")
def get_room_controller(session: Session) -> RoomController:
    return RoomController(session)


def get_test_app() -> tuple[FastAPI, TestClient]:
    from ibg.routers.user import router as user_router
    from ibg.routers.game import router as game_router
    from ibg.routers.socket import router as socket_router
    from ibg.routers.room import router as room_router
    from ibg.routers.undercover import router as undercover_router

    origins = ["*"]
    app = FastAPI(title="IBG")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(user_router)
    app.include_router(game_router)
    app.include_router(socket_router)
    app.include_router(room_router)
    app.include_router(undercover_router)

    @app.exception_handler(NoResultFound)
    async def unicorn_exception_handler(request: Request, exc: NoResultFound):
        return JSONResponse(
            status_code=404,
            content={"message": "Couldn't find requested resource"},
        )

    @app.exception_handler(BaseError)
    async def base_error_exception_handler(request: Request, exc: BaseError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "name": exc.name,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    return app, TestClient(app)
