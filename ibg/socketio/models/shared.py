import socketio
from aredis_om import JsonModel
from sqlmodel import Session

from ibg.api.controllers.game import GameController
from ibg.api.controllers.room import RoomController
from ibg.api.controllers.undercover import UndercoverController
from ibg.api.controllers.user import UserController
from ibg.database import create_app_engine, get_redis_om_connection


class IBGSocket(socketio.AsyncServer):
    def __init__(self):

        from ibg.socketio.controllers.room import SocketRoomController  # Import here to avoid circular import

        super().__init__(async_mode="asgi", cors_allowed_origins="*")
        with Session(create_app_engine()) as session:
            self.room_controller = RoomController(session)
            self.game_controller = GameController(session)
            self.user_controller = UserController(session)
            self.undercover_controller = UndercoverController(session)
            self.socket_room_controller = SocketRoomController(
                self.room_controller,
                self.game_controller,
                self.user_controller,
                self.undercover_controller,
            )


redis_connection = get_redis_om_connection()


class RedisJsonModel(JsonModel):
    class Meta:
        database = redis_connection
