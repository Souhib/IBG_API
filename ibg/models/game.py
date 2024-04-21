from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, JSON
from sqlmodel import Field

from ibg.models.shared import DBModel


class GameType(str, Enum):
    UNDERCOVER = "undercover"
    CODENAMES = "codenames"


class GameBase(DBModel):
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    number_of_players: int = Field(gt=0)
    type: GameType
    game_configurations: dict | None = Field(
        default_factory=dict, sa_column=Column(JSON)
    )


class GameCreate(GameBase):
    room_id: UUID


class GameUpdate(DBModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    number_of_players: int | None = None
    type: GameType | None = None
    game_configurations: dict | None = None
