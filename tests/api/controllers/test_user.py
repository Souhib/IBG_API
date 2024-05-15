import random

import pycountry
import pytest
from faker import Faker
from sqlmodel import Session, select

from ibg.api.controllers.user import UserController
from ibg.api.models.error import UserAlreadyExistsError, UserNotFoundError
from ibg.api.models.table import User
from ibg.api.models.user import UserCreate, UserUpdate


@pytest.mark.asyncio
async def test_creates_new_user_with_valid_input(user_controller: UserController, session: Session, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )

    # Act
    result = await user_controller.create_user(user_create)
    db_user = session.exec(select(User).where(User.id == result.id)).one()

    # Assert
    assert result.username == user_create.username == db_user.username
    assert result.email_address == user_create.email_address == db_user.email_address
    assert result.country == user_create.country == db_user.country
    assert result.password == user_create.password == db_user.password
    assert db_user.id == result.id


@pytest.mark.asyncio
async def test_create_two_users_with_same_email_address(user_controller: UserController, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )

    # Act
    await user_controller.create_user(user_create)

    # Assert
    with pytest.raises(UserAlreadyExistsError):
        await user_controller.create_user(user_create)


@pytest.mark.asyncio
async def test_raises_exception_if_user_create_is_none(user_controller: UserController):
    with pytest.raises(Exception):
        await user_controller.create_user(None)


@pytest.mark.asyncio
async def test_empty_list_when_no_users(user_controller: UserController):
    # Arrange

    # Act
    result = await user_controller.get_users()

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_list_few_users(user_controller: UserController, faker: Faker):
    # Arrange
    users = [
        UserCreate(
            username=faker.user_name(),
            email_address=faker.email(),
            country=random.choice([country.alpha_3 for country in pycountry.countries]),
            password=faker.password(),
        )
        for _ in range(5)
    ]
    # Act
    created_users = [await user_controller.create_user(user) for user in users]
    db_users = await user_controller.get_users()

    # Assert
    assert len(db_users) == 5
    for user, created_user, db_user in zip(users, created_users, db_users):
        assert user.username == created_user.username == db_user.username
        assert user.email_address == created_user.email_address == db_user.email_address
        assert user.country == created_user.country == db_user.country
        assert user.password == created_user.password == db_user.password


@pytest.mark.asyncio
async def test_returns_user_with_valid_uuid(user_controller: UserController, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    new_user = await user_controller.create_user(user_create)

    # Act
    result = await user_controller.get_user_by_id(new_user.id)

    # Assert
    assert result.id == new_user.id
    assert result.username == user_create.username == new_user.username
    assert result.email_address == user_create.email_address == new_user.email_address
    assert result.country == user_create.country == new_user.country
    assert result.password == user_create.password == new_user.password


@pytest.mark.asyncio
async def test_update_user_with_valid_input(user_controller: UserController, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    new_user = await user_controller.create_user(user_create)

    user_update = UserUpdate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
    )

    # Act
    updated_user = await user_controller.update_user_by_id(new_user.id, user_update)

    # Assert
    assert updated_user.id == new_user.id
    assert updated_user.username == user_update.username
    assert updated_user.email_address == user_update.email_address
    assert updated_user.country == user_update.country


@pytest.mark.asyncio
async def test_update_user_with_invalid_user_id(user_controller: UserController, faker: Faker):
    # Arrange
    user_update = UserUpdate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
    )

    # Act & Assert
    with pytest.raises(UserNotFoundError, match="User with id .* not found"):
        await user_controller.update_user_by_id(faker.uuid4(), user_update)


@pytest.mark.asyncio
async def test_delete_user(user_controller: UserController, session: Session, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    new_user = await user_controller.create_user(user_create)

    # Act
    await user_controller.delete_user(new_user.id)

    # Assert
    with pytest.raises(UserNotFoundError, match="User with id .* not found"):
        await user_controller.get_user_by_id(new_user.id)


@pytest.mark.asyncio
async def test_delete_user_bad_behavior(user_controller: UserController, faker: Faker):
    # Arrange
    non_existent_id = faker.uuid4()

    # Act & Assert
    with pytest.raises(UserNotFoundError, match="User with id .* not found"):
        await user_controller.delete_user(non_existent_id)


@pytest.mark.asyncio
async def test_update_user_password(user_controller: UserController, session: Session, faker: Faker):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email_address=faker.email(),
        country=random.choice([country.alpha_3 for country in pycountry.countries]),
        password=faker.password(),
    )
    new_user = await user_controller.create_user(user_create)

    new_password = faker.password()

    # Act
    updated_user = await user_controller.update_user_password(new_user.id, new_password)

    # Assert
    assert updated_user.id == new_user.id
    assert updated_user.username == new_user.username
    assert updated_user.email_address == new_user.email_address
    assert updated_user.country == new_user.country
    assert updated_user.password == new_password


@pytest.mark.asyncio
async def test_update_user_password_that_doesnt_exist(user_controller: UserController, faker: Faker):
    # Arrange
    non_existent_id = faker.uuid4()
    new_password = faker.password()

    # Act & Assert
    with pytest.raises(UserNotFoundError, match="User with id .* not found"):
        await user_controller.update_user_password(non_existent_id, new_password)
