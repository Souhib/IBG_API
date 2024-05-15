from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from ibg.api.controllers.room import RoomController
from ibg.api.models.room import RoomCreate, RoomJoin, RoomLeave
from ibg.api.models.view import RoomView
from ibg.dependencies import get_room_controller

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=RoomView, status_code=HTTP_201_CREATED)
async def create_room(
    *,
    room_create: RoomCreate,
    room_controller: RoomController = Depends(get_room_controller),
) -> RoomView:
    return RoomView.model_validate(await room_controller.create_room(room_create))


@router.get("", response_model=list[RoomView])
async def get_all_rooms(
    *,
    room_controller: RoomController = Depends(get_room_controller),
) -> list[RoomView]:
    return [RoomView.model_validate(room) for room in await room_controller.get_rooms()]


@router.get("/{room_id}", response_model=RoomView)
async def get_room(
    *,
    room_id: UUID,
    room_controller: RoomController = Depends(get_room_controller),
) -> RoomView:
    return RoomView.model_validate(await room_controller.get_room_by_id(room_id))


@router.patch("/join", response_model=RoomView)
async def join_room(
    *,
    room_join: RoomJoin,
    room_controller: RoomController = Depends(get_room_controller),
) -> RoomView:
    return RoomView.model_validate(await room_controller.join_room(room_join))


@router.patch("/leave", response_model=RoomView)
async def leave_room(
    *,
    room_leave: RoomLeave,
    room_controller: RoomController = Depends(get_room_controller),
) -> RoomView:
    return RoomView.model_validate(await room_controller.leave_room(room_leave))


@router.delete("/{room_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_room(
    *,
    room_id: UUID,
    room_controller: RoomController = Depends(get_room_controller),
) -> None:
    await room_controller.delete_room(room_id)
