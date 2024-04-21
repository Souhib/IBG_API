import datetime
import random
import string
from uuid import uuid4

import pycountry
import pytest
from faker import Faker
from freezegun import freeze_time
from sqlalchemy.exc import NoResultFound
from sqlmodel import select, Session

from ibg.controllers.game import GameController
from ibg.controllers.room import RoomController
from ibg.controllers.user import UserController
from ibg.models.errors import ErrorRoomIsNotActive
from ibg.models.room import RoomType, RoomStatus, RoomCreate
from ibg.models.game import GameType, GameCreate, GameUpdate
from ibg.models.models import Game
from ibg.models.user import UserCreate


@pytest.mark.asyncio
async def test_create_game(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    game_create = GameCreate(
        room_id=room.id,
        type=GameType.UNDERCOVER,
        number_of_players=faker.random_int(min=4, max=10),
    )
    now = datetime.datetime.now()
    with freeze_time(now):
        game = await game_controller.create_game(game_create)
        assert game.room_id == room.id
        assert game.type == game_create.type
        assert game.number_of_players == game_create.number_of_players
        assert game.start_time == now
        assert game.end_time is None


@pytest.mark.asyncio
async def test_create_multiple_games(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    games = []
    for _ in range(3):
        game_create = GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
        games.append(await game_controller.create_game(game_create))
    result = game_controller.session.exec(select(Game)).all()
    assert len(result) == 3
    for game, db_game in zip(games, result):
        assert game.room_id == db_game.room_id
        assert game.type == db_game.type
        assert game.number_of_players == db_game.number_of_players
        assert game.start_time == db_game.start_time
        assert game.end_time == db_game.end_time


@pytest.mark.asyncio
async def test_create_multiple_games_in_different_rooms(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    rooms = []
    games = []
    for _ in range(3):
        room = await room_controller.create_room(
            RoomCreate(
                owner_id=owner.id,
                password="".join(random.choice(string.digits) for _ in range(4)),
                status=RoomStatus.ONLINE,
            )
        )
        rooms.append(room)
        game_create = GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
        games.append(await game_controller.create_game(game_create))
    result = game_controller.session.exec(select(Game)).all()
    assert len(result) == 3
    for game, db_game in zip(games, result):
        assert game.room_id == db_game.room_id
        assert game.type == db_game.type
        assert game.number_of_players == db_game.number_of_players
        assert game.start_time == db_game.start_time
        assert game.end_time == db_game.end_time


@pytest.mark.asyncio
async def test_def_create_game_raises_exception_if_room_does_not_exist(
    user_controller: UserController,
    game_controller: GameController,
    faker: Faker,
):
    _ = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(NoResultFound):
        await game_controller.create_game(
            GameCreate(
                room_id=uuid4(),
                type=GameType.UNDERCOVER,
                number_of_players=faker.random_int(min=4, max=10),
            )
        )


@pytest.mark.asyncio
async def test_def_create_game_raises_exception_if_room_is_not_active(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    session: Session,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.OFFLINE,
        )
    )
    room.type = RoomType.INACTIVE
    session.add(room)
    session.commit()
    with pytest.raises(
        ErrorRoomIsNotActive, match=f"Room with id {room.id} is not active"
    ):
        _ = await game_controller.create_game(
            GameCreate(
                room_id=room.id,
                type=GameType.UNDERCOVER,
                number_of_players=faker.random_int(min=4, max=10),
            )
        )


@pytest.mark.asyncio
async def test_get_all_games(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    games = []
    for _ in range(3):
        game_create = GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
        games.append(await game_controller.create_game(game_create))
    result = await game_controller.get_games()
    assert len(result) == 3
    for game, db_game in zip(games, result):
        assert game.room_id == db_game.room_id
        assert game.type == db_game.type
        assert game.number_of_players == db_game.number_of_players
        assert game.start_time == db_game.start_time
        assert game.end_time == db_game.end_time


@pytest.mark.asyncio
async def test_get_game_by_id(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    game_create = GameCreate(
        room_id=room.id,
        type=GameType.UNDERCOVER,
        number_of_players=faker.random_int(min=4, max=10),
    )
    game = await game_controller.create_game(game_create)
    result = await game_controller.get_game_by_id(game.id)
    assert game.room_id == result.room_id
    assert game.type == result.type
    assert game.number_of_players == result.number_of_players
    assert game.start_time == result.start_time
    assert game.end_time == result.end_time


@pytest.mark.asyncio
async def test_get_game_by_id_raises_exception_if_game_does_not_exist(
    user_controller: UserController,
    game_controller: GameController,
    faker: Faker,
):
    _ = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(NoResultFound):
        await game_controller.get_game_by_id(uuid4())


@pytest.mark.asyncio
async def test_update_game(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    game_create = GameCreate(
        room_id=room.id,
        type=GameType.UNDERCOVER,
        number_of_players=faker.random_int(min=4, max=10),
    )
    game = await game_controller.create_game(game_create)
    new_number_of_players = faker.random_int(min=4, max=10)
    updated_game = await game_controller.update_game(
        game.id, GameUpdate(number_of_players=new_number_of_players)
    )
    assert updated_game.room_id == game.room_id
    assert updated_game.type == game.type
    assert updated_game.number_of_players == new_number_of_players
    assert updated_game.start_time == game.start_time
    assert updated_game.end_time == game.end_time


@pytest.mark.asyncio
async def test_update_game_raises_exception_if_game_does_not_exist(
    user_controller: UserController,
    game_controller: GameController,
    faker: Faker,
):
    _ = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(NoResultFound):
        await game_controller.update_game(
            uuid4(), GameUpdate(number_of_players=faker.random_int(min=4, max=10))
        )


@pytest.mark.asyncio
async def test_end_game(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    game_create = GameCreate(
        room_id=room.id,
        type=GameType.UNDERCOVER,
        number_of_players=faker.random_int(min=4, max=10),
    )
    game = await game_controller.create_game(game_create)
    now = datetime.datetime.now()
    with freeze_time(now):
        updated_game = await game_controller.end_game(game.id)
        assert updated_game.room_id == game.room_id
        assert updated_game.type == game.type
        assert updated_game.number_of_players == game.number_of_players
        assert updated_game.start_time == game.start_time
        assert updated_game.end_time == now


@pytest.mark.asyncio
async def test_end_game_raises_exception_if_game_does_not_exist(
    user_controller: UserController,
    game_controller: GameController,
    faker: Faker,
):
    _ = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(NoResultFound):
        await game_controller.end_game(uuid4())


@pytest.mark.asyncio
async def test_delete_game(
    user_controller: UserController,
    room_controller: RoomController,
    game_controller: GameController,
    faker: Faker,
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
            status=RoomStatus.ONLINE,
        )
    )
    game_create = GameCreate(
        room_id=room.id,
        type=GameType.UNDERCOVER,
        number_of_players=faker.random_int(min=4, max=10),
    )
    game = await game_controller.create_game(game_create)
    await game_controller.delete_game(game.id)
    with pytest.raises(NoResultFound):
        _ = await game_controller.get_game_by_id(game.id)


@pytest.mark.asyncio
async def test_delete_game_raises_exception_if_game_does_not_exist(
    game_controller: GameController, faker: Faker
):
    with pytest.raises(NoResultFound):
        await game_controller.delete_game(uuid4())


# @pytest.mark.asyncio
# async def test_get_games(user_controller: UserController, room_controller: RoomController, game_controller: GameController, faker: Faker):
#    owner = await user_controller.create_user(
#        UserCreate(
#            username=faker.user_name(),
#            email_address=faker.email(),
#            country=random.choice([country.alpha_3 for country in pycountry.countries]),
#            password=faker.password(),
#        )
#    )
#    room = await room_controller.create_room(
#        RoomCreate(
#            owner_id=owner.id,
#            password=''.join(random.choice(string.digits) for _ in range(4)),
#            status=RoomStatus.ONLINE,
#        )
#    )
#    games = []
#    for _ in range(3):
#        game_create = GameCreate(
#            room_id=room.id,
#            type=GameType.UNDERCOVER,
#            number_of_players=faker.random_int(min=4, max=10),
#        )
#        games.append(await game_controller.create_game(game_create))
#    result = await game_controller.get_games()
#    assert len(result) == 3
#    for game, db_game in zip(games, result):
#        assert game.room_id == db_game.room_id
#        assert game.type == db_game.type
#        assert game.number_of_players == db_game.number_of_players
#        assert game.start_time == db_game.start_time
#        assert game.end_time == db_game.end_time
