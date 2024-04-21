from typing import Sequence
from uuid import UUID

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from ibg.controllers.shared import create_random_public_id
from ibg.models.errors import (
    UserNotInRoomError,
    WrongRoomPasswordError,
    UserAlreadyInRoomError,
    RoomNotFoundError,
    UserNotFoundError,
)
from ibg.models.relationship import RoomUserLink
from ibg.models.room import RoomType, RoomCreate, RoomJoin, RoomLeave
from ibg.models.models import Room, User


class RoomController:
    def __init__(self, session: Session):
        self.session = session

    async def create_room(self, room_create: RoomCreate) -> Room:
        active_room = await self._get_all_active_rooms()
        room_public_id = create_random_public_id()
        while any(room.public_id == room_public_id for room in active_room):
            room_public_id = create_random_public_id()
        new_room = Room(**room_create.model_dump(), public_id=room_public_id)
        room_user_link = RoomUserLink(room_id=new_room.id, user_id=new_room.owner_id)
        self.session.add(new_room)
        self.session.add(room_user_link)
        self.session.commit()
        self.session.refresh(new_room)
        return new_room

    async def _get_all_active_rooms(self) -> Sequence[Room]:
        return self.session.exec(select(Room).where(Room.type == RoomType.ACTIVE)).all()

    async def get_rooms(self) -> Sequence[Room]:
        """
        Get all rooms. If no rooms exist, return an empty list.
        :return: A list of all rooms.
        """
        return self.session.exec(select(Room)).all()

    async def get_room_by_id(self, room_id: UUID) -> Room:
        """
        Get a room by its id. If the room does not exist, raise a NoResultFound exception.
        :param room_id: The id of the room to get.
        :return: The room.
        """
        try:
            return self.session.get_one(Room, room_id)
        except NoResultFound:
            raise RoomNotFoundError(room_id=room_id)

    async def delete_room(self, room_id: UUID) -> None:
        """
        Delete a room by its id. If the room does not exist, raise a NoResultFound exception.
        :param room_id: The id of the room to delete.
        :return: None
        """
        try:
            db_room = self.session.get_one(Room, room_id)
            self.session.delete(db_room)
            self.session.commit()
        except NoResultFound:
            raise RoomNotFoundError(room_id=room_id)

    async def join_room(self, room_join: RoomJoin) -> Room:
        """
        Add a user to a room. If the room does not exist, raise a NoResultFound exception. If the password is incorrect, raise a WrongRoomPasswordError.
        :param room_join: The room and user to join.
        :return: The updated room.
        """
        try:
            db_room = self.session.get_one(Room, room_join.room_id)
        except NoResultFound:
            raise RoomNotFoundError(room_id=room_join.room_id)
        if db_room.password != room_join.password:
            raise WrongRoomPasswordError(room_id=room_join.room_id)
        existing_link = self.session.exec(
            select(RoomUserLink).where(
                RoomUserLink.room_id == room_join.room_id,
                RoomUserLink.user_id == room_join.user_id,
                RoomUserLink.connected == True,  # noqa: E712
            )
        ).first()
        if existing_link:
            raise UserAlreadyInRoomError(
                user_id=room_join.user_id, room_id=room_join.room_id
            )
        user_room_link = RoomUserLink(
            room_id=room_join.room_id, user_id=room_join.user_id
        )
        self.session.add(user_room_link)
        self.session.commit()
        self.session.refresh(db_room)
        return db_room

    async def leave_room(self, room_leave: RoomLeave) -> Room:
        """
        Remove a user from a room. If the room does not exist, raise a NoResultFound exception.
        If the user is not in the room, raise a UserNotInRoomError.
        If the user is the owner of the room, set the room to inactive.

        :param room_leave: The room and user to leave.
        :return: The updated room.
        """
        try:
            db_room = self.session.exec(
                select(Room).where(Room.id == room_leave.room_id)
            ).one()
        except NoResultFound:
            raise RoomNotFoundError(room_id=room_leave.room_id)

        try:
            db_user = self.session.exec(
                select(User).where(User.id == room_leave.user_id)
            ).one()
        except NoResultFound:
            raise UserNotFoundError(user_id=room_leave.user_id)

        if not any(user_room_link.id == db_user.id for user_room_link in db_room.users):
            raise UserNotInRoomError(user_id=db_user.id, room_id=room_leave.room_id)  # type: ignore
        if db_room.owner_id == db_user.id:
            db_room.type = RoomType.INACTIVE
            self.session.add(db_room)

        try:
            user_room_link = self.session.exec(
                select(RoomUserLink)
                .where(RoomUserLink.room_id == room_leave.room_id)
                .where(RoomUserLink.user_id == db_user.id)
            ).one()
        except NoResultFound:
            raise UserNotInRoomError(user_id=db_user.id, room_id=room_leave.room_id)  # type: ignore
        if user_room_link.connected:
            user_room_link.connected = False
        else:
            raise UserNotInRoomError(user_id=db_user.id, room_id=room_leave.room_id)  # type: ignore
        self.session.add(user_room_link)
        self.session.commit()
        self.session.refresh(db_room)
        return db_room
