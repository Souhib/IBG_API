import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from sqlalchemy.exc import NoResultFound
from starlette.testclient import TestClient

from ibg.api.controllers.user import UserController
from ibg.api.models.error import UserAlreadyExistsError
from ibg.api.models.table import User
from ibg.dependencies import get_user_controller


@pytest.mark.asyncio
async def test_get_user_by_id(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    def _mock_get_user_by_id():
        user_controller.get_user_by_id = AsyncMock(
            return_value=User(
                id=_id,
                username="JohnDoe",
                email_address="john.doe@test.com",
                country="FRA",
                password="securepassword",
            )
        )
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_get_user_by_id

    get_user_route_response = client.get(f"/users/{_id}")
    assert get_user_route_response.status_code == 200
    assert get_user_route_response.json() == {
        "id": str(_id),
        "username": "JohnDoe",
        "email_address": "john.doe@test.com",
        "country": "FRA",
    }


@pytest.mark.asyncio
async def test_get_user_by_id_raise_no_result_found(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    def _mock_get_user_by_id():
        user_controller.get_user_by_id = AsyncMock(side_effect=NoResultFound)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_get_user_by_id

    get_user_route_response = client.get(f"/users/{_id}")
    assert get_user_route_response.status_code == 404
    assert get_user_route_response.json() == {"message": "Couldn't find requested resource"}


@pytest.mark.asyncio
async def test_get_users(user_controller: UserController, app: FastAPI, client: TestClient):

    mock_users = [
        User(
            id=uuid.uuid4(),
            username="JohnDoe",
            email_address="john.doe@test.com",
            country="FRA",
            password="securepassword",
        ),
        User(
            id=uuid.uuid4(),
            username="JaneDoe",
            email_address="jane.doe@test.com",
            country="FRA",
            password="securepassword",
        ),
    ]

    def _mock_get_users():
        user_controller.get_users = AsyncMock(return_value=mock_users)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_get_users

    get_users_route_response = client.get("/users")
    assert get_users_route_response.status_code == 200
    assert get_users_route_response.json() == [
        {
            "id": str(user.id),
            "username": user.username,
            "email_address": user.email_address,
            "country": user.country,
        }
        for user in mock_users
    ]


@pytest.mark.asyncio
async def test_create_user(user_controller: UserController, app: FastAPI, client: TestClient):

    user_data = {
        "username": "JohnDoe",
        "email_address": "john.doe@test.com",
        "country": "FRA",
        "password": "securepassword",
    }

    mock_user = User(id=uuid.uuid4(), **user_data)

    def _mock_create_user():
        user_controller.create_user = AsyncMock(return_value=mock_user)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_create_user

    create_user_route_response = client.post("/users", json=user_data)
    assert create_user_route_response.status_code == 201
    assert create_user_route_response.json() == {
        "id": str(mock_user.id),
        "username": mock_user.username,
        "email_address": mock_user.email_address,
        "country": mock_user.country,
    }


@pytest.mark.asyncio
async def test_create_user_user_already_exists(user_controller: UserController, app: FastAPI, client: TestClient):

    user_data = {
        "username": "JohnDoe",
        "email_address": "john.doe@test.com",
        "country": "FRA",
        "password": "securepassword",
    }

    def _mock_create_user():
        user_controller.create_user = AsyncMock(
            side_effect=UserAlreadyExistsError(email_address=user_data["email_address"])
        )
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_create_user

    create_user_route_response = client.post("/users", json=user_data)
    assert create_user_route_response.status_code == 409
    assert create_user_route_response.json() == {
        "name": "UserAlreadyExistsError",
        "message": f"User with email address {user_data['email_address']} already exists",
        "status_code": 409,
    }


@pytest.mark.asyncio
async def test_create_user_invalid_username(user_controller: UserController, app: FastAPI, client: TestClient):

    user_data = {
        "username": "",  # Invalid username
        "email_address": "john.doe@test.com",
        "country": "FRA",
        "password": "securepassword",
    }

    def _mock_create_user():
        user_controller.create_user = AsyncMock(side_effect=ValueError)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_create_user

    create_user_route_response = client.post("/users", json=user_data)
    assert create_user_route_response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_bad_country(user_controller: UserController, app: FastAPI, client: TestClient):

    user_data = {
        "username": "JohnDoe",
        "email_address": "john.doe@test.com",
        "country": "XYZ",
        "password": "securepassword",
    }

    def _mock_create_user():
        user_controller.create_user = AsyncMock(side_effect=ValueError)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_create_user

    create_user_route_response = client.post("/users", json=user_data)
    assert create_user_route_response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_by_id(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    user_update_data = {
        "username": "UpdatedJohnDoe",
        "email_address": "updated.john.doe@test.com",
        "country": "USA",
    }

    updated_user = User(
        id=_id,
        **user_update_data,
        password="securepassword",  # password is not updated
    )

    def _mock_update_user_by_id():
        user_controller.update_user_by_id = AsyncMock(return_value=updated_user)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_update_user_by_id

    update_user_route_response = client.patch(f"/users/{_id}", json=user_update_data)
    assert update_user_route_response.status_code == 200
    assert update_user_route_response.json() == {
        "id": str(updated_user.id),
        "username": updated_user.username,
        "email_address": updated_user.email_address,
        "country": updated_user.country,
    }


@pytest.mark.asyncio
async def test_update_user_by_id_no_result_found_error(
    user_controller: UserController, app: FastAPI, client: TestClient
):
    _id = uuid.uuid4()

    user_update_data = {
        "username": "UpdatedJohnDoe",
        "email_address": "updated.john.doe@test.com",
        "country": "USA",
    }

    def _mock_update_user_by_id():
        user_controller.update_user_by_id = AsyncMock(side_effect=NoResultFound)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_update_user_by_id

    update_user_route_response = client.patch(f"/users/{_id}", json=user_update_data)
    assert update_user_route_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_by_id(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    def _mock_delete_user():
        user_controller.delete_user = AsyncMock(return_value=None)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_delete_user

    delete_user_route_response = client.delete(f"/users/{_id}")
    assert delete_user_route_response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_by_id_no_result_found(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    def _mock_delete_user():
        user_controller.delete_user = AsyncMock(side_effect=NoResultFound)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_delete_user

    delete_user_route_response = client.delete(f"/users/{_id}")
    assert delete_user_route_response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_password(user_controller: UserController, app: FastAPI, client: TestClient):
    _id = uuid.uuid4()

    password_data = {"password": "newsecurepassword"}

    updated_user = User(
        id=_id,
        username="JohnDoe",
        email_address="john.doe@test.com",
        country="FRA",
        password="newsecurepassword",
    )

    def _mock_update_user_password():
        user_controller.update_user_password = AsyncMock(return_value=updated_user)
        return user_controller

    app.dependency_overrides[get_user_controller] = _mock_update_user_password

    update_user_password_route_response = client.patch(f"/users/{_id}/password", json=password_data)
    assert update_user_password_route_response.status_code == 200
    assert update_user_password_route_response.json() == {
        "id": str(updated_user.id),
        "username": updated_user.username,
        "email_address": updated_user.email_address,
        "country": updated_user.country,
    }
