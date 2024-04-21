from datetime import datetime
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, Relationship

from ibg.models.user import UserBase, UserView
from ibg.models.relationship import RoomUserLink, RoomGameLink, UserGameLink
from ibg.models.room import RoomType, RoomBase
from ibg.models.game import GameBase


class Room(RoomBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    public_id: str = Field(min_length=5, max_length=5)
    owner_id: UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    type: RoomType = RoomType.ACTIVE
    users: list["User"] = Relationship(
        back_populates="rooms",
        link_model=RoomUserLink,
        sa_relationship_kwargs={"secondary": "roomuserlink"},
    )
    games: list["Game"] = Relationship(back_populates="room", link_model=RoomGameLink)
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


class Game(GameBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    room_id: UUID | None = Field(foreign_key="room.id")
    user_id: UUID | None = Field(foreign_key="user.id")
    room: Room = Relationship(back_populates="games", link_model=RoomGameLink)
    users: list["User"] = Relationship(back_populates="games", link_model=UserGameLink)


class User(UserBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    password: str = Field(min_length=5)
    rooms: list[Room] = Relationship(back_populates="users", link_model=RoomUserLink)
    games: list[Game] = Relationship(back_populates="users", link_model=UserGameLink)


class RoomView(RoomBase):
    id: UUID
    public_id: str
    owner_id: UUID
    password: str
    created_at: datetime
    type: RoomType
    users: list[UserView]
    games: list[Game]
