from aredis_om import NotFoundError

from ibg.api.controllers.game import GameController
from ibg.api.controllers.room import RoomController
from ibg.api.controllers.undercover import UndercoverController
from ibg.api.controllers.user import UserController
from ibg.api.models.error import RoomNotFoundError, UserAlreadyInRoomError, UserNotInRoomError
from ibg.api.models.event import EventCreate
from ibg.api.models.room import RoomCreate, RoomJoin, RoomLeave
from ibg.api.models.table import Room
from ibg.socketio.models.room import JoinRoomUser, LeaveRoomUser
from ibg.socketio.models.room import Room as RedisRoom
from ibg.socketio.models.user import User


class SocketRoomController:

    def __init__(
        self,
        room_controller: RoomController,
        game_controller: GameController,
        user_controller: UserController,
        undercover_controller: UndercoverController,
    ):
        self._room_controller = room_controller
        self._game_controller = game_controller
        self._user_controller = user_controller
        self._undercover_controller = undercover_controller

    async def user_join_room(self, sid: str, join_room_user: JoinRoomUser) -> Room:
        """
        Join a user to a room. If the room does not exist, raise a RoomNotFoundError. If the user is already in the room, raise a UserAlreadyInRoomError.
        :param sid: The socket id of the user.
        :param join_room_user: The user to join the room.
        :return: None
        """
        db_room = await self._room_controller.get_active_room_by_public_id(join_room_user.public_room_id)
        try:
            redis_room = await RedisRoom.find(RedisRoom.id == str(db_room.id)).first()
        except NotFoundError:
            raise RoomNotFoundError(room_id=join_room_user.public_room_id)
        db_user = await self._user_controller.get_user_by_id(join_room_user.user_id)
        db_room = await self._room_controller.join_room(
            RoomJoin(
                room_id=db_room.id,
                user_id=join_room_user.user_id,
                password=join_room_user.password,
            )
        )
        if any(user.id == str(db_user.id) for user in redis_room.users):
            raise UserAlreadyInRoomError(user_id=join_room_user.user_id, room_id=join_room_user.public_room_id)
        user = User(id=str(db_user.id), username=db_user.username, sid=sid)
        await user.save()
        redis_room.users.append(user)
        await redis_room.save()
        await self._room_controller.create_room_activity(
            room_id=db_room.id,
            activity_create=EventCreate(
                name="join_room",
                data={
                    "user_id": str(db_user.id),
                    "username": db_user.username,
                    "message": f"User {db_user.username} joined the room {str(db_room.id)}.",
                },
                user_id=db_user.id,
            ),
        )
        return db_room

    async def user_leave_room(self, leave_room_user: LeaveRoomUser) -> Room:
        """
        Leave a user from a room. If the room does not exist, raise a RoomNotFoundError.
        If the user is not in the room, raise a UserNotInRoomError.

        :param leave_room_user: The user to leave the room.
        :return: None
        """
        try:
            redis_room = await RedisRoom.find(RedisRoom.id == str(leave_room_user.room_id)).first()
        except NotFoundError:
            raise RoomNotFoundError(room_id=leave_room_user.room_id)
        db_user = await self._user_controller.get_user_by_id(leave_room_user.user_id)
        if not any(user.id == str(db_user.id) for user in redis_room.users):
            raise UserNotInRoomError(user_id=leave_room_user.user_id, room_id=leave_room_user.room_id)
        db_room = await self._room_controller.leave_room(
            RoomLeave(room_id=leave_room_user.room_id, user_id=leave_room_user.user_id)
        )
        # Check that the user is not currently in a game within the room TODO - Implement this
        # if any(game['players'] == leave_room_user.user_id for game in rooms[leave_room_user.room_id]["games"]):
        #    raise UserInGameError(user_id=leave_room_user.user_id, room_id=leave_room_user.room_id)
        redis_room.users.remove(User(id=str(db_user.id), username=db_user.username))
        await redis_room.save()
        redis_user = await User.find(User.id == str(db_user.id)).first()
        await redis_user.delete()
        await self._room_controller.create_room_activity(
            room_id=leave_room_user.room_id,
            activity_create=EventCreate(
                name="leave_room",
                data={
                    "user_id": db_user.id,
                    "username": db_user.username,
                    "message": f"User {db_user.username} left the room {db_room.id}.",
                },
                user_id=db_user.id,
            ),
        )
        return redis_room

    async def create_room(self, sid, room_create: RoomCreate) -> Room:
        """
        Create a room with the given room_id. If the room already exists, raise a RoomAlreadyExistsError.

        :param sid: The socket id of the user.
        :param room_create: The room to create.
        :return: Room
        """
        db_user = await self._user_controller.get_user_by_id(room_create.owner_id)
        db_room = await self._room_controller.create_room(room_create)
        redis_user = User(id=str(db_user.id), username=db_user.username, sid=sid)
        await redis_user.save()
        redis_room = RedisRoom(id=str(db_room.id), users=[redis_user])
        await redis_room.save()
        return db_room
