import random
import re

import pycountry
import pytest
from faker import Faker
from sqlmodel import Session, select

from ibg.api.controllers.room import RoomController
from ibg.api.controllers.user import UserController
from ibg.api.models.table import User
from ibg.api.models.user import UserCreate
from tests.sockets.conftest import TestUserClient, server_required


@pytest.mark.asyncio
@server_required()
async def test_socket_create_room(
    user_controller: UserController,
    session: Session,
    faker: Faker,
    clear_database_and_redis
):
    socket_user = TestUserClient()
    await socket_user.connect()

    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )

    user = await user_controller.create_user(user_create)
    password = "".join([str(random.randint(0, 9)) for _ in range(4)])

    assert socket_user.client.sid is not None

    await socket_user.client.call(
        "create_room",
        {"owner_id": str(user.id), "status": "online", "password": password},
    )

    assert socket_user.responses["new_room_created"]
    assert socket_user.responses["new_room_created"]["data"]
    assert socket_user.responses["new_room_created"]["data"]["status"] == "online"
    assert socket_user.responses["new_room_created"]["data"]["password"] == password
    assert socket_user.responses["new_room_created"]["data"]["owner_id"] == str(user.id)
    assert socket_user.responses["new_room_created"]["data"]["type"] == "active"
    assert socket_user.responses["new_room_created"]["data"]["id"]
    assert socket_user.responses["new_room_created"]["data"]["created_at"]
    assert socket_user.responses["new_room_created"]["data"]["public_id"]
    assert re.match(
        r"Room [a-f0-9\-]+ created\.",
        socket_user.responses["new_room_created"]["message"],
    )
    assert socket_user.responses["new_room_created"]["data"]["users"]
    assert socket_user.responses["new_room_created"]["data"]["games"] == []


@pytest.mark.asyncio
@server_required()
async def test_socket_create_multiple_rooms_with_different_users(
    user_controller: UserController,
    session: Session,
    faker: Faker,
    clear_database_and_redis
):
    # Prepare
    clients = []
    users = []
    for _ in range(3):
        client = TestUserClient()
        await client.connect()
        clients.append(client)
        user_create = UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
        user = await user_controller.create_user(user_create)
        users.append(user)

    # Act
    for client in clients:
        password = "".join([str(random.randint(0, 9)) for _ in range(4)])
        await client.client.call(
            "create_room",
            {"owner_id": str(users[clients.index(client)].id), "status": "online", "password": password},
        )
        assert client.responses["new_room_created"]
        assert client.responses["new_room_created"]["data"]
        assert client.responses["new_room_created"]["data"]["status"] == "online"
        assert client.responses["new_room_created"]["data"]["password"] == password
        assert client.responses["new_room_created"]["data"]["owner_id"] == str(users[clients.index(client)].id)
        assert client.responses["new_room_created"]["data"]["type"] == "active"
        assert client.responses["new_room_created"]["data"]["id"]
        assert client.responses["new_room_created"]["data"]["created_at"]
        assert client.responses["new_room_created"]["data"]["public_id"]
        assert re.match(
            r"Room [a-f0-9\-]+ created\.",
            client.responses["new_room_created"]["message"],
        )
        assert client.responses["new_room_created"]["data"]["users"]
        assert client.responses["new_room_created"]["data"]["games"] == []


@pytest.mark.asyncio
@server_required()
async def test_socket_join_room(
    user_controller: UserController,
    room_controller: RoomController,
    faker: Faker,
    clear_database_and_redis
):
    clients = []
    users = []
    for _ in range(3):
        client = TestUserClient()
        await client.connect()
        clients.append(client)
        user_create = UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
        user = await user_controller.create_user(user_create)
        users.append(user)

    password = "".join([str(random.randint(0, 9)) for _ in range(4)])
    await clients[0].client.call(
        "create_room",
        {"owner_id": str(users[0].id), "status": "online", "password": password},
    )

    for client in clients[1:]:
        await client.client.call(
            "join_room",
            {"room_id": clients[0].responses["new_room_created"]["data"]["id"], "password": password},
        )
        assert client.responses["room_joined"]
        assert client.responses["room_joined"]["data"]
        assert client.responses["room_joined"]["data"]["status"] == "online"

