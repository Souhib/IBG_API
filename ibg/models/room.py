from enum import Enum
from uuid import UUID

from ibg.models.shared import DBModel


class RoomType(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RoomStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"


class RoomBase(DBModel):
    status: RoomStatus


class RoomCreate(RoomBase):
    owner_id: UUID
    password: str


class RoomJoin(DBModel):
    room_id: UUID
    user_id: UUID
    password: str


class RoomLeave(DBModel):
    room_id: UUID
    user_id: UUID
