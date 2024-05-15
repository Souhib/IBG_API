from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy.exc import NoResultFound
from starlette.testclient import TestClient

from ibg.api.controllers.game import GameController
from ibg.api.models.error import ErrorRoomIsNotActive
from ibg.api.models.game import GameType
from ibg.api.models.table import Game
from ibg.dependencies import get_game_controller


@pytest.mark.asyncio
async def test_get_games(game_controller: GameController, app: FastAPI, client: TestClient):

    games_id = [uuid4() for _ in range(3)]

    room_id = uuid4()
    user_id = uuid4()
    start_time = datetime.now()
    end_time = datetime.now()

    mock_games = [
        Game(
            id=games_id[0],
            room_id=room_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            number_of_players=4,
            type=GameType.UNDERCOVER,
            game_configurations={"key": "value"},
        ),
        Game(
            id=games_id[1],
            room_id=room_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            number_of_players=4,
            type=GameType.UNDERCOVER,
            game_configurations={"key": "value"},
        ),
        Game(
            id=games_id[2],
            room_id=room_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            number_of_players=4,
            type=GameType.UNDERCOVER,
            game_configurations={"key": "value"},
        ),
    ]

    def _mock_get_games():
        game_controller.get_games = AsyncMock(return_value=mock_games)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_get_games

    get_games_route_response = client.get("/games")
    assert get_games_route_response.status_code == 200
    assert get_games_route_response.json() == [
        {
            "id": str(game.id),
            "room_id": str(game.room_id),
            "user_id": str(game.user_id),
            "start_time": game.start_time.isoformat(),
            "end_time": game.end_time.isoformat(),
            "number_of_players": game.number_of_players,
            "type": game.type,
            "game_configurations": game.game_configurations,
        }
        for game in mock_games
    ]


@pytest.mark.asyncio
async def test_create_game(game_controller: GameController, app: FastAPI, client: TestClient):

    user_id = uuid4()
    start_time = datetime.now()
    end_time = datetime.now()

    game_data = {
        "room_id": uuid4(),
        "number_of_players": 4,
        "type": GameType.UNDERCOVER,
        "game_configurations": {"key": "value"},
    }

    mock_game = Game(
        id=uuid4(),
        room_id=game_data["room_id"],
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=game_data["number_of_players"],
        type=game_data["type"],
        game_configurations=game_data["game_configurations"],
    )

    def _mock_create_game():
        game_controller.create_game = AsyncMock(return_value=mock_game)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_create_game

    create_game_route_response = client.post(
        "/games",
        json={
            "room_id": str(game_data["room_id"]),
            "number_of_players": game_data["number_of_players"],
            "type": game_data["type"],
            "game_configurations": game_data["game_configurations"],
        },
    )
    assert create_game_route_response.status_code == 201
    assert create_game_route_response.json() == {
        "id": str(mock_game.id),
        "room_id": str(mock_game.room_id),
        "user_id": str(mock_game.user_id),
        "start_time": mock_game.start_time.isoformat(),
        "end_time": mock_game.end_time.isoformat(),
        "number_of_players": mock_game.number_of_players,
        "type": mock_game.type,
        "game_configurations": mock_game.game_configurations,
    }


@pytest.mark.asyncio
async def test_create_game_room_not_active(game_controller: GameController, app: FastAPI, client: TestClient):

    game_data = {
        "room_id": uuid4(),
        "number_of_players": 4,
        "type": GameType.UNDERCOVER,
        "game_configurations": {"key": "value"},
    }

    def _mock_create_game():
        game_controller.create_game = AsyncMock(side_effect=ErrorRoomIsNotActive(room_id=game_data["room_id"]))
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_create_game

    create_game_route_response = client.post(
        "/games",
        json={
            "room_id": str(game_data["room_id"]),
            "number_of_players": game_data["number_of_players"],
            "type": game_data["type"],
            "game_configurations": game_data["game_configurations"],
        },
    )
    assert create_game_route_response.status_code == 403
    assert create_game_route_response.json() == {
        "name": "ErrorRoomIsNotActive",
        "message": f"Room with id {game_data['room_id']} is not active",
        "status_code": 403,
    }


@pytest.mark.asyncio
async def test_get_game_by_id(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()
    room_id = uuid4()
    user_id = uuid4()
    start_time = datetime.now()
    end_time = datetime.now()

    mock_game = Game(
        id=game_id,
        room_id=room_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=4,
        type=GameType.UNDERCOVER,
        game_configurations={"key": "value"},
    )

    def _mock_get_game():
        game_controller.get_game_by_id = AsyncMock(return_value=mock_game)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_get_game

    get_game_route_response = client.get(f"/games/{game_id}")
    assert get_game_route_response.status_code == 200
    assert get_game_route_response.json() == {
        "id": str(mock_game.id),
        "room_id": str(mock_game.room_id),
        "user_id": str(mock_game.user_id),
        "start_time": mock_game.start_time.isoformat(),
        "end_time": mock_game.end_time.isoformat(),
        "number_of_players": mock_game.number_of_players,
        "type": mock_game.type,
        "game_configurations": mock_game.game_configurations,
    }


@pytest.mark.asyncio
async def test_get_game_by_id_no_result_found(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()

    def _mock_get_game():
        game_controller.get_game_by_id = AsyncMock(side_effect=NoResultFound)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_get_game

    get_game_route_response = client.get(f"/games/{game_id}")
    assert get_game_route_response.status_code == 404
    assert get_game_route_response.json() == {"message": "Couldn't find requested resource"}


@pytest.mark.asyncio
async def test_update_game(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()
    room_id = uuid4()
    user_id = uuid4()
    start_time = datetime.now()
    end_time = datetime.now()

    game_data = {
        "room_id": room_id,
        "number_of_players": 4,
        "type": GameType.UNDERCOVER,
        "game_configurations": {"key": "value"},
    }

    mock_game = Game(
        id=game_id,
        room_id=room_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=game_data["number_of_players"],
        type=game_data["type"],
        game_configurations=game_data["game_configurations"],
    )

    def _mock_update_game():
        game_controller.update_game = AsyncMock(return_value=mock_game)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_update_game

    update_game_route_response = client.patch(
        f"/games/{game_id}",
        json={
            "number_of_players": game_data["number_of_players"],
            "type": game_data["type"],
            "game_configurations": game_data["game_configurations"],
        },
    )
    assert update_game_route_response.status_code == 200
    assert update_game_route_response.json() == {
        "id": str(mock_game.id),
        "room_id": str(mock_game.room_id),
        "user_id": str(mock_game.user_id),
        "start_time": mock_game.start_time.isoformat(),
        "end_time": mock_game.end_time.isoformat(),
        "number_of_players": mock_game.number_of_players,
        "type": mock_game.type,
        "game_configurations": mock_game.game_configurations,
    }


@pytest.mark.asyncio
async def test_end_game(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()
    room_id = uuid4()
    user_id = uuid4()
    start_time = datetime.now()
    end_time = datetime.now()

    mock_game = Game(
        id=game_id,
        room_id=room_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        number_of_players=4,
        type=GameType.UNDERCOVER,
        game_configurations={"key": "value"},
    )

    def _mock_end_game():
        game_controller.end_game = AsyncMock(return_value=mock_game)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_end_game

    end_game_route_response = client.patch(f"/games/{game_id}/end")
    assert end_game_route_response.status_code == 200
    assert end_game_route_response.json() == {
        "id": str(mock_game.id),
        "room_id": str(mock_game.room_id),
        "user_id": str(mock_game.user_id),
        "start_time": mock_game.start_time.isoformat(),
        "end_time": mock_game.end_time.isoformat(),
        "number_of_players": mock_game.number_of_players,
        "type": mock_game.type,
        "game_configurations": mock_game.game_configurations,
    }


@pytest.mark.asyncio
async def test_end_game_no_result_found(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()

    def _mock_end_game():
        game_controller.end_game = AsyncMock(side_effect=NoResultFound)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_end_game

    end_game_route_response = client.patch(f"/games/{game_id}/end")
    assert end_game_route_response.status_code == 404
    assert end_game_route_response.json() == {"message": "Couldn't find requested resource"}


@pytest.mark.asyncio
async def test_delete_game_by_id(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()

    def _mock_delete_game():
        game_controller.delete_game = AsyncMock(return_value=None)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_delete_game

    delete_game_route_response = client.delete(f"/games/{game_id}")
    assert delete_game_route_response.status_code == 204


@pytest.mark.asyncio
async def test_delete_game_by_id_no_result_found(game_controller: GameController, app: FastAPI, client: TestClient):

    game_id = uuid4()

    def _mock_delete_game():
        game_controller.delete_game = AsyncMock(side_effect=NoResultFound)
        return game_controller

    app.dependency_overrides[get_game_controller] = _mock_delete_game

    delete_game_route_response = client.delete(f"/games/{game_id}")
    assert delete_game_route_response.status_code == 404
    assert delete_game_route_response.json() == {"message": "Couldn't find requested resource"}
