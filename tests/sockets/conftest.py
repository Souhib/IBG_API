import asyncio
import os
import time
from functools import wraps
from multiprocessing import Process

import pytest
import socketio
from aiohttp import ClientConnectorError, ClientSession
from loguru import logger
from uvicorn import Config, Server


class TestUserClient:

    def __init__(self):
        self.client = socketio.AsyncClient()
        self.responses = {}

    async def connect(self):
        await self.client.connect("http://127.0.0.1:5000")

        @self.client.on("*", namespace="*")
        async def any_event(event, sid, data):
            self.responses[event] = data


class UvicornServer(Process):

    def __init__(self, config: Config, env_vars=None):
        super().__init__()
        self.server = Server(config=config)
        self.config = config
        self.env_vars = env_vars or {}

    def stop(self) -> None:
        """
        Stop the server.

        :return: None
        """
        self.terminate()

    def run(self, *args, **kwargs) -> None:
        """
        Run the server in the subprocess.
        This method is called when the process is started.
        We don't need to call it manually.

        :param args:
        :param kwargs:
        :return: None
        """
        original_env = os.environ.copy()
        os.environ.update(self.env_vars)
        try:
            self.server.run()
        finally:
            os.environ.clear()
            os.environ.update(original_env)


async def wait_for_server(url: str, timeout: int = 15):
    """
    Wait for the server to start. This function will raise a TimeoutError if the server does not start in time.

    :param url: The URL to check
    :param timeout: The maximum time to wait
    :return: None
    """
    start_time = time.time()
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.info("Server is ready")
                        return True
        except ClientConnectorError:
            pass
        if time.time() - start_time > timeout:
            raise TimeoutError("Server did not start in time")
        await asyncio.sleep(1)


def server_required():
    """
    Decorator to wait for the server to start before running the test.

    :return: The decorator
    """

    def decorator(func) -> callable:
        """
        The actual decorator function.

        :param func: The function to decorate
        :return: The decorated function
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            """
            The wrapper function that waits for the server to start before running the test.

            :param args:
            :param kwargs:
            :return: The result of the decorated function
            """
            await wait_for_server("http://127.0.0.1:5000/docs")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture(scope="session", autouse=True, name="server")
def server(postgres, redis_host_and_port: tuple[str, int]):
    """
    Fixture to start the server before running the tests. The server will be stopped after the tests are done.

    :param postgres: The postgres fixture
    :param redis_host_and_port: The redis_host_and_port fixture
    :return: The server instance
    """

    host, port = redis_host_and_port
    config = Config("main:app", host="127.0.0.1", port=5000, log_level="debug")
    env_vars = {
        "DATABASE_URL": postgres.get_connection_url(),
        "REDIS_OM_URL": f"redis://{host}:{port}",
        "LOGFIRE_TOKEN": "fake_token",
    }
    instance = UvicornServer(config=config, env_vars=env_vars)
    instance.start()
    yield instance
    instance.stop()
