import random
import string

import pytest
from faker import Faker

from ibg.api.models.room import RoomStatus, RoomType
from ibg.api.models.table import Room


def test_room_password_with_non_digit_characters(faker: Faker):
    password = "".join(string.ascii_lowercase for _ in range(4))

    with pytest.raises(ValueError):
        _ = Room(
            owner_id=faker.uuid4(),
            type=random.choice(list(RoomType)),
            status=random.choice(list(RoomStatus)),
            password=password,
        )


def test_room_password_with_less_than_4_characters(faker: Faker):
    password = "".join(string.digits for _ in range(random.randint(1, 3)))

    with pytest.raises(ValueError):
        _ = Room(
            owner_id=faker.uuid4(),
            type=random.choice(list(RoomType)),
            status=random.choice(list(RoomStatus)),
            password=str(password),
        )
