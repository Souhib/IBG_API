from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from faker import Faker
from fastapi import FastAPI
from starlette.testclient import TestClient

from ibg.api.controllers.room import RoomController
from ibg.api.controllers.shared import create_random_public_id
from ibg.api.models.error import (
    RoomNotFoundError,
    UserAlreadyInRoomError,
    UserNotFoundError,
    UserNotInRoomError,
    WrongRoomPasswordError,
)
from ibg.api.models.game import GameType
from ibg.api.models.room import RoomStatus, RoomType
from ibg.api.models.table import Game, Room, User
from ibg.dependencies import get_room_controller


@pytest.mark.asyncio
async def test_get_rooms(room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient):
    public_id = [create_random_public_id() for _ in range(3)]
    rooms_id = [uuid4() for _ in range(3)]
    owner_id_1 = uuid4()
    created_at = faker.date_time()

    mock_rooms = [
        Room(
            id=rooms_id[0],
            public_id=public_id[0],
            owner_id=owner_id_1,
            status=RoomStatus.ONLINE,
            password="1234",
            type=RoomType.ACTIVE,
            created_at=created_at,
            users=[],
            games=[],
        ),
        Room(
            id=rooms_id[1],
            public_id=public_id[1],
            owner_id=owner_id_1,
            status=RoomStatus.ONLINE,
            password="1234",
            type=RoomType.ACTIVE,
            created_at=created_at,
            users=[],
            games=[],
        ),
        Room(
            id=rooms_id[2],
            public_id=public_id[2],
            owner_id=owner_id_1,
            status=RoomStatus.ONLINE,
            password="1234",
            type=RoomType.ACTIVE,
            created_at=created_at,
            users=[],
            games=[],
        ),
    ]

    def _mock_get_rooms():
        room_controller.get_rooms = AsyncMock(return_value=mock_rooms)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_get_rooms

    get_rooms_route_response = client.get("/rooms")
    assert get_rooms_route_response.status_code == 200
    assert get_rooms_route_response.json() == [
        {
            "id": str(rooms_id[0]),
            "public_id": public_id[0],
            "owner_id": str(owner_id_1),
            "status": RoomStatus.ONLINE.value,
            "password": "1234",
            "type": RoomType.ACTIVE.value,
            "created_at": created_at.isoformat(),
            "users": [],
            "games": [],
        },
        {
            "id": str(rooms_id[1]),
            "public_id": public_id[1],
            "owner_id": str(owner_id_1),
            "status": RoomStatus.ONLINE.value,
            "password": "1234",
            "type": RoomType.ACTIVE.value,
            "created_at": created_at.isoformat(),
            "users": [],
            "games": [],
        },
        {
            "id": str(rooms_id[2]),
            "public_id": public_id[2],
            "owner_id": str(owner_id_1),
            "status": RoomStatus.ONLINE.value,
            "password": "1234",
            "type": RoomType.ACTIVE.value,
            "created_at": created_at.isoformat(),
            "users": [],
            "games": [],
        },
    ]


@pytest.mark.asyncio
async def test_get_room(room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient):
    room_id = uuid4()
    owner_id = uuid4()
    public_id = create_random_public_id()
    created_at = faker.date_time()

    mock_room = Room(
        id=room_id,
        public_id=public_id,
        owner_id=owner_id,
        status=RoomStatus.ONLINE,
        password="1234",
        type=RoomType.ACTIVE,
        created_at=created_at,
        users=[],
        games=[],
    )

    def _mock_get_room_by_id():
        room_controller.get_room_by_id = AsyncMock(return_value=mock_room)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_get_room_by_id

    get_room_route_response = client.get(f"/rooms/{room_id}")
    assert get_room_route_response.status_code == 200
    assert get_room_route_response.json() == {
        "id": str(room_id),
        "public_id": public_id,
        "owner_id": str(owner_id),
        "status": RoomStatus.ONLINE.value,
        "password": "1234",
        "type": RoomType.ACTIVE.value,
        "created_at": created_at.isoformat(),
        "users": [],
        "games": [],
    }


@pytest.mark.asyncio
async def test_get_room_when_room_does_not_exist(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()

    def _mock_get_room_by_id():
        room_controller.get_room_by_id = AsyncMock(side_effect=RoomNotFoundError(room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_get_room_by_id

    get_room_route_response = client.get(f"/rooms/{room_id}")
    assert get_room_route_response.status_code == 404
    assert get_room_route_response.json() == {
        "status_code": 404,
        "name": "RoomNotFoundError",
        "message": f"Room with id {room_id} not found",
    }


@pytest.mark.asyncio
async def test_get_room_with_multiple_users_and_multiple_games(
    room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient
):
    room_id = uuid4()
    created_at = faker.date_time()
    start_time = faker.date_time()
    end_time = faker.date_time()
    game1_id = uuid4()
    game2_id = uuid4()
    public_id = create_random_public_id()

    user = User(
        id=uuid4(),
        username="JaneDoe",
        email_address="jane.doe@test.com",
        country="FRA",
        password="securepassword",
    )
    user2 = User(
        id=uuid4(),
        username="JohnDoe",
        email_address="john.doe@test.com",
        country="FRA",
        password="securepassword",
    )
    game1 = Game(
        id=game1_id,
        room_id=room_id,
        user_id=user.id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=2,
        type=GameType.UNDERCOVER,
        game_configurations={"key": "value"},
    )
    game2 = Game(
        id=game2_id,
        room_id=room_id,
        user_id=user2.id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=2,
        type=GameType.UNDERCOVER,
        game_configurations={"key": "value"},
    )

    mock_room = Room(
        id=room_id,
        public_id=public_id,
        owner_id=user.id,
        status=RoomStatus.ONLINE,
        password="1234",
        type=RoomType.ACTIVE,
        created_at=created_at,
        users=[user, user2],
        games=[game1, game2],
    )

    def _mock_get_room_by_id():
        room_controller.get_room_by_id = AsyncMock(return_value=mock_room)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_get_room_by_id

    get_room_route_response = client.get(f"/rooms/{room_id}")
    assert get_room_route_response.status_code == 200
    assert get_room_route_response.json() == {
        "id": str(room_id),
        "public_id": public_id,
        "owner_id": str(user.id),
        "status": RoomStatus.ONLINE.value,
        "password": "1234",
        "type": RoomType.ACTIVE.value,
        "created_at": created_at.isoformat(),
        "users": [
            {
                "id": str(user.id),
                "username": user.username,
                "email_address": user.email_address,
                "country": user.country,
            },
            {
                "id": str(user2.id),
                "username": user2.username,
                "email_address": user2.email_address,
                "country": user2.country,
            },
        ],
        "games": [
            {
                "id": str(game1.id),
                "room_id": str(room_id),
                "user_id": str(user.id),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "number_of_players": 2,
                "type": GameType.UNDERCOVER.value,
                "game_configurations": {"key": "value"},
            },
            {
                "id": str(game2.id),
                "room_id": str(room_id),
                "user_id": str(user2.id),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "number_of_players": 2,
                "type": GameType.UNDERCOVER.value,
                "game_configurations": {"key": "value"},
            },
        ],
    }


@pytest.mark.asyncio
async def test_create_room(room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient):
    room_id = uuid4()
    owner_id = uuid4()
    created_at = faker.date_time()
    public_id = create_random_public_id()

    mock_room = Room(
        id=room_id,
        public_id=public_id,
        owner_id=owner_id,
        status=RoomStatus.ONLINE,
        password="1234",
        type=RoomType.ACTIVE,
        created_at=created_at,
        users=[],
        games=[],
    )

    def _mock_create_room():
        room_controller.create_room = AsyncMock(return_value=mock_room)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_create_room

    create_room_route_response = client.post(
        "/rooms",
        json={
            "owner_id": str(owner_id),
            "status": RoomStatus.ONLINE.value,
            "password": "1234",
        },
    )
    assert create_room_route_response.status_code == 201
    assert create_room_route_response.json() == {
        "id": str(room_id),
        "public_id": public_id,
        "owner_id": str(owner_id),
        "status": RoomStatus.ONLINE.value,
        "password": "1234",
        "type": RoomType.ACTIVE.value,
        "created_at": created_at.isoformat(),
        "users": [],
        "games": [],
    }


@pytest.mark.asyncio
async def test_join_room(room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()
    password = "1234"
    public_id = create_random_public_id()

    mock_room = Room(
        id=room_id,
        public_id=public_id,
        owner_id=user_id,
        status=RoomStatus.ONLINE,
        password="1234",
        type=RoomType.ACTIVE,
        created_at=faker.date_time(),
        users=[],
        games=[],
    )

    def _mock_join_room():
        room_controller.join_room = AsyncMock(return_value=mock_room)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_join_room

    join_room_route_response = client.patch(
        "/rooms/join",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
            "password": password,
        },
    )
    assert join_room_route_response.status_code == 200
    assert join_room_route_response.json() == {
        "id": str(room_id),
        "public_id": public_id,
        "owner_id": str(user_id),
        "status": RoomStatus.ONLINE.value,
        "password": "1234",
        "type": RoomType.ACTIVE.value,
        "created_at": mock_room.created_at.isoformat(),
        "users": [],
        "games": [],
    }


@pytest.mark.asyncio
async def test_join_room_when_room_does_not_exist(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()
    password = "1234"

    def _mock_join_room():
        room_controller.join_room = AsyncMock(side_effect=RoomNotFoundError(room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_join_room

    join_room_route_response = client.patch(
        "/rooms/join",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
            "password": password,
        },
    )
    assert join_room_route_response.status_code == 404
    assert join_room_route_response.json() == {
        "status_code": 404,
        "name": "RoomNotFoundError",
        "message": f"Room with id {room_id} not found",
    }


@pytest.mark.asyncio
async def test_join_room_when_user_already_in_room(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()

    def _mock_join_room():
        room_controller.join_room = AsyncMock(side_effect=UserAlreadyInRoomError(user_id=user_id, room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_join_room

    join_room_route_response = client.patch(
        "/rooms/join",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
            "password": "1234",
        },
    )
    assert join_room_route_response.status_code == 409
    assert join_room_route_response.json() == {
        "status_code": 409,
        "name": "UserAlreadyInRoomError",
        "message": f"User with id {user_id} is already in room with id {room_id}",
    }


@pytest.mark.asyncio
async def test_leave_room(room_controller: RoomController, faker: Faker, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()
    public_id = create_random_public_id()

    mock_room = Room(
        id=room_id,
        public_id=public_id,
        owner_id=user_id,
        status=RoomStatus.ONLINE,
        password="1234",
        type=RoomType.ACTIVE,
        created_at=faker.date_time(),
        users=[],
        games=[],
    )

    def _mock_leave_room():
        room_controller.leave_room = AsyncMock(return_value=mock_room)
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_leave_room

    leave_room_route_response = client.patch(
        "/rooms/leave",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
        },
    )
    assert leave_room_route_response.status_code == 200
    assert leave_room_route_response.json() == {
        "id": str(room_id),
        "public_id": public_id,
        "owner_id": str(user_id),
        "status": RoomStatus.ONLINE.value,
        "password": "1234",
        "type": RoomType.ACTIVE.value,
        "created_at": mock_room.created_at.isoformat(),
        "users": [],
        "games": [],
    }


@pytest.mark.asyncio
async def test_leave_room_when_room_does_not_exist(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()

    def _mock_leave_room():
        room_controller.leave_room = AsyncMock(side_effect=RoomNotFoundError(room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_leave_room

    leave_room_route_response = client.patch(
        "/rooms/leave",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
        },
    )
    assert leave_room_route_response.status_code == 404
    assert leave_room_route_response.json() == {
        "status_code": 404,
        "name": "RoomNotFoundError",
        "message": f"Room with id {room_id} not found",
    }


@pytest.mark.asyncio
async def test_leave_room_when_user_not_in_room(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()

    def _mock_leave_room():
        room_controller.leave_room = AsyncMock(side_effect=UserNotInRoomError(user_id=user_id, room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_leave_room

    leave_room_route_response = client.patch(
        "/rooms/leave",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
        },
    )
    assert leave_room_route_response.status_code == 404
    assert leave_room_route_response.json() == {
        "status_code": 404,
        "name": "UserNotInRoomError",
        "message": f"User with id {user_id} is not in room with id {room_id}",
    }


@pytest.mark.asyncio
async def test_leave_room_when_user_not_found(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()

    def _mock_leave_room():
        room_controller.leave_room = AsyncMock(side_effect=UserNotFoundError(user_id=user_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_leave_room

    leave_room_route_response = client.patch(
        "/rooms/leave",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
        },
    )
    assert leave_room_route_response.status_code == 404
    assert leave_room_route_response.json() == {
        "status_code": 404,
        "name": "UserNotFoundError",
        "message": f"User with id {user_id} not found",
    }


@pytest.mark.asyncio
async def test_delete_room(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()

    def _mock_delete_room():
        room_controller.delete_room = AsyncMock()
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_delete_room

    delete_room_route_response = client.delete(f"/rooms/{room_id}")
    assert delete_room_route_response.status_code == 204


@pytest.mark.asyncio
async def test_get_room_by_id_not_found(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()

    def _mock_get_room_by_id():
        room_controller.get_room_by_id = AsyncMock(side_effect=RoomNotFoundError(room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_get_room_by_id

    get_room_route_response = client.get(f"/rooms/{room_id}")
    assert get_room_route_response.status_code == 404
    assert get_room_route_response.json() == {
        "status_code": 404,
        "name": "RoomNotFoundError",
        "message": f"Room with id {room_id} not found",
    }


@pytest.mark.asyncio
async def test_join_room_wrong_password(room_controller: RoomController, app: FastAPI, client: TestClient):
    room_id = uuid4()
    user_id = uuid4()
    password = "1234"

    def _mock_join_room():
        room_controller.join_room = AsyncMock(side_effect=WrongRoomPasswordError(room_id=room_id))
        return room_controller

    app.dependency_overrides[get_room_controller] = _mock_join_room

    join_room_route_response = client.patch(
        "/rooms/join",
        json={
            "user_id": str(user_id),
            "room_id": str(room_id),
            "password": password,
        },
    )
    assert join_room_route_response.status_code == 403
    assert join_room_route_response.json() == {
        "name": "WrongRoomPasswordError",
        "message": f"The password to join the room with id : {room_id} is incorrect",
        "status_code": 403,
    }
