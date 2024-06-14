from enum import Enum
from uuid import UUID

from pydantic import Field, field_validator

from ibg.api.models.shared import DBModel


class RoomType(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RoomStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"


class RoomBase(DBModel):
    status: RoomStatus
    password: str = Field(min_length=4, max_length=4)

    @field_validator("password")
    @classmethod
    def check_password_only_digits(cls, v: str) -> str:
        """
        It checks that the password only contains digits
        :param v: The value to be validated
        :return: The room
        """
        if not v.isdigit():
            raise ValueError("Password must only contain digits")
        return v


class RoomCreate(RoomBase):
    owner_id: UUID


class RoomJoin(DBModel):
    user_id: UUID
    room_id: UUID
    password: str


class RoomLeave(DBModel):
    room_id: UUID
    user_id: UUID
