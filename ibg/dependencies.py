from fastapi import Depends
from sqlmodel import Session

from ibg.api.controllers.game import GameController
from ibg.api.controllers.room import RoomController
from ibg.api.controllers.undercover import UndercoverController
from ibg.api.controllers.user import UserController
from ibg.database import create_app_engine


def get_session():
    engine = create_app_engine()
    with Session(engine) as session:
        yield session


def get_user_controller(session: Session = Depends(get_session)) -> UserController:
    return UserController(session)


def get_room_controller(session: Session = Depends(get_session)) -> RoomController:
    return RoomController(session)


def get_game_controller(session: Session = Depends(get_session)) -> GameController:
    return GameController(session)


def get_undercover_controller(
    session: Session = Depends(get_session),
) -> UndercoverController:
    return UndercoverController(session)
