from datetime import datetime
from uuid import UUID

from sqlmodel import Field
from ibg.models.shared import DBModel


class RoomUserLink(DBModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID | None = Field(default=None, foreign_key="room.id")
    user_id: UUID | None = Field(default=None, foreign_key="user.id")
    joined_at: datetime = Field(default_factory=datetime.now)
    connected: bool = Field(default=True)


class RoomGameLink(DBModel, table=True):
    room_id: UUID | None = Field(default=None, foreign_key="room.id", primary_key=True)
    game_id: UUID | None = Field(default=None, foreign_key="game.id", primary_key=True)


class UserGameLink(DBModel, table=True):
    user_id: UUID | None = Field(default=None, foreign_key="user.id", primary_key=True)
    game_id: UUID | None = Field(default=None, foreign_key="game.id", primary_key=True)
