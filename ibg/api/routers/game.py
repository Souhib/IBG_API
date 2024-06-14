from uuid import UUID

from fastapi import APIRouter, Depends

from ibg.api.controllers.game import GameController
from ibg.api.models.game import GameCreate, GameUpdate
from ibg.api.models.table import Game
from ibg.dependencies import get_game_controller

router = APIRouter(
    prefix="/games",
    tags=["games"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=Game, status_code=201)
async def create_game(
    *,
    game_create: GameCreate,
    game_controller: GameController = Depends(get_game_controller),
) -> Game:
    return Game.model_validate(await game_controller.create_game(game_create))


@router.get("", response_model=list[Game])
async def get_all_undercover_games(
    *,
    game_controller: GameController = Depends(get_game_controller),
) -> list[Game]:
    return [Game.model_validate(game) for game in await game_controller.get_games()]


@router.get("/{game_id}", response_model=Game)
async def get_undercover_game(
    *,
    game_id: UUID,
    game_controller: GameController = Depends(get_game_controller),
) -> Game:
    return Game.model_validate(await game_controller.get_game_by_id(game_id))


@router.patch("/{game_id}", response_model=Game)
async def update_undercover_game(
    *,
    game_id: UUID,
    game_update: GameUpdate,
    game_controller: GameController = Depends(get_game_controller),
) -> Game:
    return Game.model_validate(await game_controller.update_game(game_id, game_update))


@router.patch("/{game_id}/end", response_model=Game)
async def end_undercover_game(
    *,
    game_id: UUID,
    game_controller: GameController = Depends(get_game_controller),
) -> Game:
    return Game.model_validate(await game_controller.end_game(game_id))


@router.delete("/{game_id}", status_code=204)
async def delete_undercover_game(
    *,
    game_id: UUID,
    game_controller: GameController = Depends(get_game_controller),
):
    await game_controller.delete_game(game_id)


# @router.post("/{game_id}/turns", response_model=Turn, status_code=201)
# async def create_turn(
#     *,
#     game_id: UUID,
#     game_controller: GameController = Depends(get_game_controller),
# ) -> Game:
#     return Game.model_validate(await game_controller.create_turn(game_id))
#
#
# @router.post("/{game_id}/events", response_model=Turn, status_code=201)
# async def create_event(
#     *,
#     game_id: UUID,
#     event_create: EventCreate,
#     game_controller: GameController = Depends(get_game_controller),
# ) -> Game:
#     return Game.model_validate(await game_controller.create_turn_event(game_id, event_create))
