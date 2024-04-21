from fastapi import Depends
from sqlmodel import Session

from ibg.controllers.game import GameController
from ibg.controllers.room import RoomController
from ibg.controllers.undercover import UndercoverController
from ibg.controllers.user import UserController
from ibg.database import create_app_engine


def get_session():
    engine = create_app_engine()
    with Session(engine) as session:
        yield session


def get_user_controller(session: Session = Depends(get_session)):
    return UserController(session)


def get_room_controller(session: Session = Depends(get_session)):
    return RoomController(session)


def get_game_controller(session: Session = Depends(get_session)):
    return GameController(session)


def get_undercover_controller(session: Session = Depends(get_session)):
    return UndercoverController(session)
