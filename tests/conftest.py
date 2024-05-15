import os

import pytest
import redis
from faker import Faker
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine
from sqlmodel import Session, SQLModel
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer

from ibg.api.controllers.game import GameController
from ibg.api.controllers.room import RoomController
from ibg.api.controllers.undercover import UndercoverController
from ibg.api.controllers.user import UserController


@pytest.fixture(name="faker")
def get_faker() -> Faker:
    return Faker("fr_FR")


@pytest.fixture(name="postgres", scope="session", autouse=True)
def generate_test_pgsql():
    with PostgresContainer("postgres:latest") as postgres:
        postgres.with_env("POSTGRES_USER", "test")
        postgres.with_env("POSTGRES_PASSWORD", "testpassword")
        postgres.with_env("POSTGRES_DB", "testdb")
        yield postgres


@pytest.fixture(name="engine", scope="session", autouse=True)
def generate_socket_test_pgsql_engine(postgres):
    engine = create_engine(postgres.get_connection_url())
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def generate_test_db_session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture(name="redis_container", scope="session", autouse=True)
def redis_container() -> DockerContainer:
    with DockerContainer("redislabs/redisearch:latest").with_exposed_ports(6379) as container:
        yield container


@pytest.fixture(name="redis_host_and_port", scope="session", autouse=True)
def redis_host_and_port(redis_container: DockerContainer) -> tuple[str, int]:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    yield host, port


@pytest.fixture(autouse=True)
def clear_database_and_redis(engine: Engine, redis_host_and_port: tuple[str, int], request):
    yield
    # We check if the test is a controller test to avoid dropping the database, we're doing this for performance reasons
    if "controller" in str(request.node.fspath):
        host, port = redis_host_and_port
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        if "sockets" in str(request.node.fspath):
            r = redis.Redis(host=host, port=port, db=0)
            r.flushdb()
            for key in r.scan_iter("ibg:*"):
                r.delete(key)


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


@pytest.fixture(name="app", scope="session")
def get_test_app(postgres: PostgresContainer, redis_host_and_port: tuple[str, int]) -> FastAPI:
    host, port = redis_host_and_port
    os.environ["DATABASE_URL"] = postgres.get_connection_url()
    os.environ["REDIS_OM_URL"] = f"redis://{host}:{port}"
    os.environ["LOGFIRE_TOKEN"] = "fake_token"
    from ibg.app import create_app  # Import here because environment variables need to be set before importing the app
    from main import lifespan  # Import here because environment variables need to be set before importing the app

    app = create_app(lifespan=lifespan)
    return app
