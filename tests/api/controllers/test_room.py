import random
import string

import pycountry
import pytest
from faker import Faker
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ibg.api.controllers.room import RoomController
from ibg.api.controllers.user import UserController
from ibg.api.models.error import (
    RoomNotFoundError,
    UserAlreadyInRoomError,
    UserNotFoundError,
    UserNotInRoomError,
    WrongRoomPasswordError,
)
from ibg.api.models.relationship import RoomUserLink
from ibg.api.models.room import RoomCreate, RoomJoin, RoomLeave, RoomStatus, RoomType
from ibg.api.models.user import UserCreate


@pytest.mark.asyncio
async def test_create_room_with_valid_owner_and_password(
    user_controller: UserController,
    room_controller: RoomController,
    faker: Faker,
    session: Session,
):
    # Arrange
    owner = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    owner = await user_controller.create_user(owner)
    room_create = RoomCreate(
        status=random.choice(list(RoomStatus)),
        owner_id=owner.id,
        password="".join(random.choice(string.digits) for _ in range(4)),
    )

    # Act
    room = await room_controller.create_room(room_create=room_create)
    db_room = await room_controller.get_room_by_id(room.id)
    room_user_link = session.exec(select(RoomUserLink).where(RoomUserLink.room_id == room.id)).one()

    # Assert
    assert room.owner_id == owner.id == db_room.owner_id
    assert room.status == room_create.status == db_room.status
    assert room.type == db_room.type
    assert room.password == room_create.password == db_room.password
    assert room.id is not None
    assert room.id == db_room.id
    assert room.public_id == db_room.public_id
    assert room_user_link.room_id == room.id
    assert room_user_link.user_id == owner.id


@pytest.mark.asyncio
async def test_join_existing_room(user_controller: UserController, room_controller: RoomController, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    owner_of_the_room_user = await user_controller.create_user(user_create)
    room_create = RoomCreate(
        status=random.choice(list(RoomStatus)),
        owner_id=owner_of_the_room_user.id,
        password="".join(random.choice(string.digits) for _ in range(4)),
    )
    user_to_join_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    user_to_join = await user_controller.create_user(user_to_join_create)
    room = await room_controller.create_room(room_create=room_create)

    # Act
    updated_room = await room_controller.join_room(
        RoomJoin(room_id=room.id, user_id=user_to_join.id, password=room.password)
    )

    # Assert
    joined_user = await user_controller.get_user_by_id(user_to_join.id)

    # I want you to check all the users in the room and see if the user we just added is in the room
    assert joined_user in updated_room.users
    assert updated_room.owner_id == owner_of_the_room_user.id == room.owner_id
    assert updated_room.status == room_create.status == room.status
    assert updated_room.type == room.type
    assert updated_room.password == room_create.password == room.password
    assert updated_room.id == room.id
    assert updated_room.public_id == room.public_id


@pytest.mark.asyncio
async def test_join_then_leave_and_join_again_a_room(
    user_controller: UserController, room_controller: RoomController, faker: Faker
):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    owner_of_the_room_user = await user_controller.create_user(user_create)
    room_create = RoomCreate(
        status=random.choice(list(RoomStatus)),
        owner_id=owner_of_the_room_user.id,
        password="".join(random.choice(string.digits) for _ in range(4)),
    )
    user_to_join_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    user_to_join = await user_controller.create_user(user_to_join_create)
    room = await room_controller.create_room(room_create=room_create)

    # Act
    _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user_to_join.id, password=room.password))
    _ = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=user_to_join.id))
    updated_room = await room_controller.join_room(
        RoomJoin(room_id=room.id, user_id=user_to_join.id, password=room.password)
    )

    # Assert
    joined_user = await user_controller.get_user_by_id(user_to_join.id)
    assert joined_user in updated_room.users
    assert updated_room.owner_id == owner_of_the_room_user.id == room.owner_id
    assert updated_room.status == room_create.status == room.status
    assert updated_room.type == room.type
    assert updated_room.password == room_create.password == room.password
    assert updated_room.id == room.id
    assert updated_room.public_id == room.public_id


@pytest.mark.asyncio
async def test_join_room_twice(user_controller: UserController, room_controller: RoomController, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    owner_of_the_room_user = await user_controller.create_user(user_create)
    room_create = RoomCreate(
        status=random.choice(list(RoomStatus)),
        owner_id=owner_of_the_room_user.id,
        password="".join(random.choice(string.digits) for _ in range(4)),
    )
    user_to_join_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    user_to_join = await user_controller.create_user(user_to_join_create)
    room = await room_controller.create_room(room_create=room_create)

    # Act
    _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user_to_join.id, password=room.password))
    with pytest.raises(
        UserAlreadyInRoomError,
        match=f"User with id {user_to_join.id} is already in room with id {room.id}",
    ):
        _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user_to_join.id, password=room.password))


@pytest.mark.asyncio
async def test_join_room_to_nonexistent_room(
    user_controller: UserController, room_controller: RoomController, faker: Faker
):
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    user = await user_controller.create_user(user_create)
    with pytest.raises(RoomNotFoundError):
        await room_controller.join_room(
            RoomJoin(
                room_id=user.id,
                user_id=user.id,
                password="".join(random.choice(string.digits) for _ in range(4)),
            )
        )


@pytest.mark.asyncio
async def test_create_room_user_non_existent_owner(
    user_controller: UserController, room_controller: RoomController, faker: Faker
):
    room_create = RoomCreate(
        status=random.choice(list(RoomStatus)),
        owner_id=faker.uuid4(),
        password="".join(random.choice(string.digits) for _ in range(4)),
    )
    with pytest.raises(IntegrityError):
        _ = await room_controller.create_room(room_create=room_create)


@pytest.mark.asyncio
async def test_get_empty_list_rooms(room_controller: RoomController):
    rooms = await room_controller.get_rooms()
    assert rooms == []


@pytest.mark.asyncio
async def test_get_rooms(user_controller: UserController, room_controller: RoomController, faker: Faker):
    users = [
        await user_controller.create_user(
            UserCreate(
                username=faker.user_name(),
                email_address=faker.email(),
                country=random.choice([country.alpha_3 for country in pycountry.countries]),
                password=faker.password(),
            )
        )
        for _ in range(3)
    ]
    create_rooms = [
        await room_controller.create_room(
            RoomCreate(
                status=random.choice(list(RoomStatus)),
                owner_id=user.id,
                password="".join(random.choice(string.digits) for _ in range(4)),
            )
        )
        for user in users
    ]
    db_rooms = await room_controller.get_rooms()
    assert len(db_rooms) == 3
    assert db_rooms[0].owner_id == users[0].id
    assert db_rooms[0].status == create_rooms[0].status
    assert db_rooms[0].type == create_rooms[0].type
    assert db_rooms[0].password == create_rooms[0].password
    assert db_rooms[0].id == create_rooms[0].id
    assert db_rooms[0].public_id == create_rooms[0].public_id
    assert db_rooms[1].owner_id == users[1].id
    assert db_rooms[1].status == create_rooms[1].status
    assert db_rooms[1].type == create_rooms[1].type
    assert db_rooms[1].password == create_rooms[1].password
    assert db_rooms[1].id == create_rooms[1].id
    assert db_rooms[1].public_id == create_rooms[1].public_id
    assert db_rooms[2].public_id == create_rooms[2].public_id
    assert db_rooms[2].owner_id == users[2].id
    assert db_rooms[2].status == create_rooms[2].status
    assert db_rooms[2].type == create_rooms[2].type
    assert db_rooms[2].password == create_rooms[2].password
    assert db_rooms[2].id == create_rooms[2].id


@pytest.mark.asyncio
async def test_get_room_by_id(user_controller: UserController, room_controller: RoomController, faker: Faker):
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            status=random.choice(list(RoomStatus)),
            owner_id=user.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    db_room = await room_controller.get_room_by_id(room.id)
    assert db_room.owner_id == user.id
    assert db_room.status == room.status
    assert db_room.type == room.type
    assert db_room.password == room.password
    assert db_room.id == room.id
    assert db_room.public_id == room.public_id


@pytest.mark.asyncio
async def test_get_non_existent_room(room_controller: RoomController, faker: Faker):
    with pytest.raises(RoomNotFoundError):
        await room_controller.get_room_by_id(faker.uuid4())


@pytest.mark.asyncio
async def test_delete_room(user_controller: UserController, room_controller: RoomController, faker: Faker):
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            status=random.choice(list(RoomStatus)),
            owner_id=user.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    await room_controller.delete_room(room_id=room.id)
    with pytest.raises(RoomNotFoundError):
        await room_controller.get_room_by_id(room.id)


@pytest.mark.asyncio
async def test_delete_non_existent_room(room_controller: RoomController, faker: Faker):
    with pytest.raises(RoomNotFoundError):
        await room_controller.delete_room(faker.uuid4())


@pytest.mark.asyncio
async def test_leave_room(user_controller: UserController, room_controller: RoomController, faker: Faker):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user.id, password=room.password))
    leaved_room = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=user.id))
    assert owner in leaved_room.users
    assert user in leaved_room.users
    assert leaved_room.owner_id == room.owner_id
    assert leaved_room.status == room.status
    assert leaved_room.type == room.type
    assert leaved_room.password == room.password
    assert leaved_room.id == room.id
    assert leaved_room.games == []
    assert leaved_room.public_id == room.public_id


@pytest.mark.asyncio
async def test_leave_non_existent_room(room_controller: RoomController, faker: Faker):
    with pytest.raises(RoomNotFoundError):
        _ = await room_controller.leave_room(RoomLeave(room_id=faker.uuid4(), user_id=faker.uuid4()))


@pytest.mark.asyncio
async def test_leave_twice(user_controller: UserController, room_controller: RoomController, faker: Faker):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user.id, password=room.password))
    _ = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=user.id))
    with pytest.raises(UserNotInRoomError):
        _ = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=user.id))


@pytest.mark.asyncio
async def test_leave_room_non_existent_user(
    user_controller: UserController, room_controller: RoomController, faker: Faker
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
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    with pytest.raises(UserNotFoundError):
        _ = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=faker.uuid4()))


@pytest.mark.asyncio
async def test_leave_room_non_existent_room(
    user_controller: UserController, room_controller: RoomController, faker: Faker
):
    owner = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    room = await room_controller.create_room(
        RoomCreate(
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    _ = await room_controller.join_room(RoomJoin(room_id=room.id, user_id=user.id, password=room.password))
    with pytest.raises(RoomNotFoundError):
        _ = await room_controller.leave_room(RoomLeave(room_id=faker.uuid4(), user_id=user.id))


@pytest.mark.asyncio
async def test_leave_room_owner(
    user_controller: UserController,
    room_controller: RoomController,
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
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    empty_room = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=owner.id))
    room_user_link = session.exec(select(RoomUserLink).where(RoomUserLink.room_id == room.id)).one()

    assert empty_room.status == room.status
    assert empty_room.owner_id == owner.id
    assert empty_room.status == room.status
    assert empty_room.type == RoomType.INACTIVE
    assert empty_room.password == room.password
    assert empty_room.id == room.id
    assert empty_room.games == []
    assert empty_room.public_id == room.public_id
    assert room_user_link.connected is False


@pytest.mark.asyncio
async def test_join_room_wrong_password(user_controller: UserController, room_controller: RoomController, faker: Faker):
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
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(WrongRoomPasswordError):
        _ = await room_controller.join_room(
            RoomJoin(
                room_id=room.id,
                user_id=user.id,
                password="".join(random.choice(string.ascii_lowercase) for _ in range(4)),
            )
        )


@pytest.mark.asyncio
async def test_leave_room_user_not_in(user_controller: UserController, room_controller: RoomController, faker: Faker):
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
            status=random.choice(list(RoomStatus)),
            owner_id=owner.id,
            password="".join(random.choice(string.digits) for _ in range(4)),
        )
    )
    user = await user_controller.create_user(
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
    )
    with pytest.raises(UserNotInRoomError):
        _ = await room_controller.leave_room(RoomLeave(room_id=room.id, user_id=user.id))
