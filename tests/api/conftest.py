import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient


@pytest.fixture(name="client")
def get_app_fixture(app: FastAPI) -> TestClient:
    return TestClient(app)
