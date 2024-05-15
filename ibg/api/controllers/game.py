from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, desc, select

from ibg.api.models.error import ErrorRoomIsNotActive, GameNotFoundError, NoTurnInsideGameError
from ibg.api.models.event import EventCreate
from ibg.api.models.game import GameCreate, GameUpdate
from ibg.api.models.relationship import GameTurnLink, RoomGameLink, TurnEventLink, UserGameLink
from ibg.api.models.room import RoomType
from ibg.api.models.table import Event, Game, Room, Turn


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
        room: Room = self.session.exec(select(Room).where(Room.id == new_game.room_id)).one()
        if room.type != RoomType.ACTIVE:
            raise ErrorRoomIsNotActive(room_id=room.id)  # type: ignore
        self.session.add(new_game)
        self.session.commit()
        self.session.refresh(new_game)
        room_game_link = RoomGameLink(room_id=new_game.room_id, game_id=new_game.id)
        for user in room.users:
            user_game_link = UserGameLink(user_id=user.id, game_id=new_game.id)
            self.session.add(user_game_link)
        self.session.add(room_game_link)
        self.session.commit()
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

    async def update_game(self, game_id: UUID, game_update: GameUpdate) -> Game:
        """
        Update a game. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to update.
        :param game_update: The updated game.
        :return: The updated game.
        """
        db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
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
        db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
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
        db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
        self.session.delete(db_game)
        self.session.commit()

    async def create_turn(self, game_id: UUID) -> Turn:
        """
        Create a turn. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to create a turn for.
        :return: None
        """
        try:
            db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
            turn = Turn(
                game_id=db_game.id,
            )
            self.session.add(turn)
            self.session.commit()
            self.session.refresh(turn)
            turn_game_link = GameTurnLink(game_id=db_game.id, turn_id=turn.id)
            self.session.add(turn_game_link)
            self.session.commit()
            return turn
        except NoResultFound:
            raise GameNotFoundError(game_id=game_id)

    async def create_turn_event(self, game_id: UUID, event_create: EventCreate) -> Event:
        """
        Create an event. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to create an event for.
        :param event_create: The event to create.
        :return: Event (TurnEvent or RoomEvent)
        """
        try:
            db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
            if not db_game.turns:
                raise NoTurnInsideGameError(game_id=game_id)
            latest_turn = self.session.exec(
                select(Turn).where(Turn.game_id == db_game.id).order_by(desc(Turn.start_time))
            ).first()
            event = Event(
                turn_id=latest_turn.id,
                name=event_create.name,
                data=event_create.data,
                user_id=event_create.user_id,
            )
            self.session.add(event)
            self.session.commit()
            self.session.refresh(event)
            turn_event_link = TurnEventLink(turn_id=latest_turn.id, event_id=event.id)
            self.session.add(turn_event_link)
            self.session.commit()
            return event
        except NoResultFound:
            raise GameNotFoundError(game_id=game_id)

    async def get_latest_turn(self, game_id: UUID) -> Turn:
        """
        Get the latest turn. If the game does not exist, raise a NoResultFound exception.

        :param game_id: The id of the game to get the latest turn for.
        :return: Turn
        """
        try:
            db_game = self.session.exec(select(Game).where(Game.id == game_id)).one()
            if not db_game.turns:
                raise NoTurnInsideGameError(game_id=game_id)
            return self.session.exec(
                select(Turn).where(Turn.game_id == db_game.id).order_by(desc(Turn.start_time))
            ).first()
        except NoResultFound:
            raise GameNotFoundError(game_id=game_id)
