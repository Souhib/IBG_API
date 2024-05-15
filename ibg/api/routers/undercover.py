from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends

from ibg.api.controllers.undercover import UndercoverController
from ibg.api.models.undercover import TermPair, TermPairCreate, Word, WordCreate
from ibg.dependencies import get_undercover_controller

router = APIRouter(
    prefix="/undercover",
    tags=["undercover"],
    responses={404: {"description": "Not found"}},
)


@router.post("/words", response_model=Word, status_code=201)
async def create_word(
    *,
    word_create: WordCreate,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> Word:
    return await undercover_controller.create_word(word_create)


@router.get("/words", response_model=Sequence[Word])
async def get_all_words(
    *,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> Sequence[Word]:
    return await undercover_controller.get_words()


@router.get("/words/{word_id}", response_model=Word)
async def get_word_by_id(
    *,
    word_id: UUID,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> Word:
    return await undercover_controller.get_word_by_id(word_id)


@router.get("/words/search/{word}", response_model=Word)
async def get_word_by_word(
    *,
    word: str,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> Word:
    return await undercover_controller.get_word_by_word(word)


@router.delete("/words/{word_id}", response_model=None, status_code=204)
async def delete_word(
    *,
    word_id: UUID,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> None:
    await undercover_controller.delete_word(word_id)


@router.post("/termpair", response_model=TermPair, status_code=201)
async def create_term_pair(
    *,
    term_pair_create: TermPairCreate,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> TermPair:
    return await undercover_controller.create_term_pair(term_pair_create.word1_id, term_pair_create.word2_id)


@router.get("/termpair", response_model=Sequence[TermPair])
async def get_all_term_pairs(
    *,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> Sequence[TermPair]:
    return await undercover_controller.get_term_pairs()


@router.get("/termpair/{term_pair_id}", response_model=TermPair)
async def get_term_pair_by_id(
    *,
    term_pair_id: UUID,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> TermPair:
    return await undercover_controller.get_term_pair_by_id(term_pair_id)


@router.get("/termpair/search/random", response_model=TermPair)
async def get_random_term_pair(
    *,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> TermPair:
    return await undercover_controller.get_random_term_pair()


@router.delete("/termpair/{term_pair_id}", response_model=None, status_code=204)
async def delete_term_pair(
    *,
    term_pair_id: UUID,
    undercover_controller: UndercoverController = Depends(get_undercover_controller),
) -> None:
    await undercover_controller.delete_term_pair(term_pair_id)
