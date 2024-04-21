from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from ibg.models.errors import ErrorRoomIsNotActive
from ibg.models.relationship import (
    RoomGameLink,
    UserGameLink,
)
from ibg.models.room import RoomType
from ibg.models.game import GameCreate, GameUpdate
from ibg.models.models import Room, Game


class GameController:
    def __init__(self, session: Session):
        self.session = session

    async def create_game(self, game_create: GameCreate) -> Game:
        """
        Create a game. If the room is not active, raise an ErrorRoomIsNotActive exception.

        :param game_create: The game to create.
        :return: The created game.
        """
        new_game = Game(**game_create.model_dump())
        room: Room = self.session.get_one(Room, new_game.room_id)
        if room.type != RoomType.ACTIVE:
            raise ErrorRoomIsNotActive(room_id=room.id)  # type: ignore
        room_game_link = RoomGameLink(room_id=new_game.room_id, game_id=new_game.id)
        for user in room.users:
            user_game_link = UserGameLink(user_id=user.id, game_id=new_game.id)
            self.session.add(user_game_link)
        self.session.add(new_game)
        self.session.add(room_game_link)
        self.session.commit()
        self.session.refresh(new_game)
        return new_game

    async def get_games(self) -> Sequence[Game]:
        """
        Get all games. If no games exist, return an empty list.

        :return: A list of all games.
        """
        return self.session.exec(select(Game)).all()

    async def get_game_by_id(self, game_id: UUID) -> Game:
        """
        Get a game by its id. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to get.
        :return: The game.
        """
        return self.session.exec(select(Game).where(Game.id == game_id)).one()

    async def update_game(self, game_id: UUID, game_update: GameUpdate):
        """
        Update a game. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to update.
        :param game_update: The updated game.
        :return:
        """
        db_game = self.session.get_one(Game, game_id)
        db_game_data = game_update.model_dump(exclude_unset=True)
        db_game.sqlmodel_update(db_game_data)
        self.session.add(db_game)
        self.session.commit()
        self.session.refresh(db_game)
        return db_game

    async def end_game(self, game_id: UUID) -> Game:
        """
        End a game. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to end.
        :return: The ended game.
        """
        db_game = self.session.get_one(Game, game_id)
        db_game.end_time = datetime.now()
        self.session.add(db_game)
        self.session.commit()
        self.session.refresh(db_game)
        return db_game

    async def delete_game(self, game_id: UUID) -> None:
        """
        Delete a game. If the game does not exist, raise a NoResultFound exception. If the room is not active, raise an ErrorRoomIsNotActive exception.

        :param game_id: The id of the game to delete.
        :return: None
        """
        db_game = self.session.get_one(Game, game_id)
        self.session.delete(db_game)
        self.session.commit()
