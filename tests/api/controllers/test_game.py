import datetime
import random
import string
from uuid import uuid4

import pycountry
import pytest
from faker import Faker
from freezegun import freeze_time
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from ibg.api.controllers.game import GameController
from ibg.api.controllers.room import RoomController
from ibg.api.controllers.user import UserController
from ibg.api.models.error import (
    ErrorRoomIsNotActive,
    GameNotFoundError,
    NoTurnInsideGameError,
    RoomNotFoundError,
    UserNotFoundError,
)
from ibg.api.models.event import EventCreate
from ibg.api.models.game import GameCreate, GameType, GameUpdate
from ibg.api.models.room import RoomCreate, RoomStatus, RoomType
from ibg.api.models.table import Game
from ibg.api.models.user import UserCreate


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
    game = await game_controller.create_game(game_create)
    assert game.room_id == room.id
    assert game.type == game_create.type
    assert game.number_of_players == game_create.number_of_players
    assert game.start_time is not None
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
    rooms = []
    games = []
    for _ in range(3):
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
    with pytest.raises(ErrorRoomIsNotActive, match=f"Room with id {room.id} is not active"):
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
    updated_game = await game_controller.update_game(game.id, GameUpdate(number_of_players=new_number_of_players))
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
        await game_controller.update_game(uuid4(), GameUpdate(number_of_players=faker.random_int(min=4, max=10)))


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
async def test_delete_game_raises_exception_if_game_does_not_exist(game_controller: GameController, faker: Faker):
    with pytest.raises(NoResultFound):
        await game_controller.delete_game(uuid4())


@pytest.mark.asyncio
async def test_create_turn(
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
    game = await game_controller.create_game(
        GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
    )
    turn = await game_controller.create_turn(game.id)
    assert turn.game_id == game.id
    assert turn.start_time is not None
    assert turn.end_time is None
    assert turn.completed is False
    assert turn.game.id == game.id
    assert turn.game.room_id == game.room_id
    assert turn.game.type == game.type
    assert turn.game.number_of_players == game.number_of_players
    assert turn.game.start_time == game.start_time
    assert turn.game.end_time == game.end_time


@pytest.mark.asyncio
async def test_create_turn_raises_exception_if_game_does_not_exist(
    game_controller: GameController,
):
    with pytest.raises(GameNotFoundError):
        await game_controller.create_turn(uuid4())


@pytest.mark.asyncio
async def test_create_turn_event(
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
    game = await game_controller.create_game(
        GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
    )
    turn = await game_controller.create_turn(game.id)
    event_name = faker.word()
    event_create = EventCreate(name=event_name, data={"key": "value"}, user_id=owner.id)
    event = await game_controller.create_turn_event(game_id=game.id, event_create=event_create)
    assert event.turn_id == turn.id
    assert event.name == event_name
    assert event.data == {"key": "value"}
    assert event.timestamp is not None
    assert event.turn.id == turn.id
    assert event.turn.game_id == turn.game_id
    assert event.turn.start_time == turn.start_time
    assert event.turn.end_time == turn.end_time
    assert event.turn.completed == turn.completed


@pytest.mark.asyncio
async def test_create_turn_event_raises_exception_if_game_does_not_exist(
    game_controller: GameController,
):
    with pytest.raises(GameNotFoundError):
        await game_controller.create_turn_event(
            game_id=uuid4(),
            event_create=EventCreate(name="event", data={"key": "value"}, user_id=uuid4()),
        )


@pytest.mark.asyncio
async def test_create_event_raises_exception_if_game_does_not_have_turn(
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
    game = await game_controller.create_game(
        GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
    )
    with pytest.raises(NoTurnInsideGameError):
        await game_controller.create_turn_event(
            game_id=game.id,
            event_create=EventCreate(name="event", data={"key": "value"}, user_id=uuid4()),
        )


@pytest.mark.asyncio
async def test_get_latest_turn(
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
    game = await game_controller.create_game(
        GameCreate(
            room_id=room.id,
            type=GameType.UNDERCOVER,
            number_of_players=faker.random_int(min=4, max=10),
        )
    )
    _ = await game_controller.create_turn(game.id)
    _ = await game_controller.create_turn(game.id)
    turn3 = await game_controller.create_turn(game.id)
    latest_turn = await game_controller.get_latest_turn(game.id)
    assert latest_turn.id == turn3.id
    assert latest_turn.start_time == turn3.start_time
    assert latest_turn.end_time == turn3.end_time
    assert latest_turn.completed == turn3.completed
    assert latest_turn.game_id == turn3.game_id


@pytest.mark.asyncio
async def test_get_latest_turn_raises_exception_if_game_does_not_exist(
    game_controller: GameController,
):
    with pytest.raises(GameNotFoundError):
        await game_controller.get_latest_turn(uuid4())


@pytest.mark.asyncio
async def test_create_room_activity(
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
    activity_name = faker.word()
    activity_create = EventCreate(name=activity_name, data={"key": "value"}, user_id=owner.id)
    activity = await room_controller.create_room_activity(room_id=room.id, activity_create=activity_create)
    assert activity.room_id == room.id
    assert activity.name == activity_name
    assert activity.data == {"key": "value"}
    assert activity.timestamp is not None
    assert activity.room.id == room.id
    assert activity.room.owner_id == room.owner_id
    assert activity.room.password == room.password
    assert activity.room.status == room.status
    assert activity.room.type == room.type
    assert activity.room.created_at == room.created_at


@pytest.mark.asyncio
async def test_create_room_activity_raises_exception_if_room_does_not_exist(
    room_controller: RoomController,
):
    with pytest.raises(RoomNotFoundError):
        await room_controller.create_room_activity(
            room_id=uuid4(),
            activity_create=EventCreate(name="activity", data={"key": "value"}, user_id=uuid4()),
        )


@pytest.mark.asyncio
async def test_create_room_activity_raises_exception_if_user_does_not_exist(
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
    with pytest.raises(UserNotFoundError):
        await room_controller.create_room_activity(
            room_id=room.id,
            activity_create=EventCreate(name="activity", data={"key": "value"}, user_id=uuid4()),
        )
