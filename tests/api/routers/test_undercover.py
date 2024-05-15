from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from faker import Faker
from fastapi import FastAPI
from starlette.testclient import TestClient

from ibg.api.controllers.undercover import UndercoverController
from ibg.api.models.error import TermPairNotFoundError, WordAlreadyExistsError, WordNotFoundErrorId
from ibg.api.models.undercover import TermPair, Word
from ibg.dependencies import get_undercover_controller


@pytest.mark.asyncio
async def test_create_word(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word_id = uuid4()
    word_create = {
        "word": faker.word(),
        "category": faker.word(),
        "short_description": faker.sentence(),
        "long_description": faker.sentence(),
    }

    def _mock_join_room():
        undercover_controller.create_word = AsyncMock(return_value=Word(id=word_id, **word_create))
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.post("/undercover/words", json=word_create)
    assert response.status_code == 201
    assert response.json() == {"id": str(word_id), **word_create}


@pytest.mark.asyncio
async def test_create_word_already_exists(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word_create = {
        "word": faker.word(),
        "category": faker.word(),
        "short_description": faker.sentence(),
        "long_description": faker.sentence(),
    }

    def _mock_join_room():
        undercover_controller.create_word = AsyncMock(side_effect=WordAlreadyExistsError(word=word_create["word"]))
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.post("/undercover/words", json=word_create)
    assert response.status_code == 409
    assert response.json() == {
        "name": "WordAlreadyExistsError",
        "message": f"Word {word_create['word']} already exists",
        "status_code": 409,
    }


@pytest.mark.asyncio
async def test_get_all_words(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    words = [
        Word(
            id=uuid4(),
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.sentence(),
        )
        for _ in range(3)
    ]

    def _mock_join_room():
        undercover_controller.get_words = AsyncMock(return_value=words)
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get("/undercover/words")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(words[0].id),
            "word": words[0].word,
            "category": words[0].category,
            "short_description": words[0].short_description,
            "long_description": words[0].long_description,
        },
        {
            "id": str(words[1].id),
            "word": words[1].word,
            "category": words[1].category,
            "short_description": words[1].short_description,
            "long_description": words[1].long_description,
        },
        {
            "id": str(words[2].id),
            "word": words[2].word,
            "category": words[2].category,
            "short_description": words[2].short_description,
            "long_description": words[2].long_description,
        },
    ]


@pytest.mark.asyncio
async def test_get_word_by_id(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word_id = uuid4()
    word = Word(
        id=word_id,
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.sentence(),
    )

    def _mock_join_room():
        undercover_controller.get_word_by_id = AsyncMock(return_value=word)
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/words/{word_id}")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(word_id),
        "word": word.word,
        "category": word.category,
        "short_description": word.short_description,
        "long_description": word.long_description,
    }


@pytest.mark.asyncio
async def test_get_word_by_id_not_found(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word_id = uuid4()

    def _mock_join_room():
        undercover_controller.get_word_by_id = AsyncMock(side_effect=WordNotFoundErrorId(word_id=word_id))
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/words/{word_id}")
    assert response.status_code == 404
    assert response.json() == {
        "name": "WordNotFoundError",
        "message": f"Word with id {word_id} not found",
        "status_code": 404,
    }


@pytest.mark.asyncio
async def test_get_word_by_word(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word = Word(
        id=uuid4(),
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.sentence(),
    )

    def _mock_join_room():
        undercover_controller.get_word_by_word = AsyncMock(return_value=word)
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/words/search/{word.word}")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(word.id),
        "word": word.word,
        "category": word.category,
        "short_description": word.short_description,
        "long_description": word.long_description,
    }


@pytest.mark.asyncio
async def test_get_word_by_word_not_found(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word = faker.word()

    def _mock_join_room():
        undercover_controller.get_word_by_word = AsyncMock(side_effect=WordNotFoundErrorId(word_id=word))
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/words/search/{word}")
    assert response.status_code == 404
    assert response.json() == {
        "name": "WordNotFoundError",
        "message": f"Word with id {word} not found",
        "status_code": 404,
    }


@pytest.mark.asyncio
async def test_delete_word(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    word_id = uuid4()

    def _mock_join_room():
        undercover_controller.delete_word = AsyncMock()
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.delete(f"/undercover/words/{word_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_term_pair(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair_id = uuid4()
    word1_id = uuid4()
    word2_id = uuid4()

    def _mock_join_room():
        undercover_controller.create_term_pair = AsyncMock(
            return_value=TermPair(id=term_pair_id, word1_id=word1_id, word2_id=word2_id)
        )
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.post(
        "/undercover/termpair",
        json={"word1_id": str(word1_id), "word2_id": str(word2_id)},
    )
    assert response.status_code == 201
    assert response.json() == {
        "id": str(term_pair_id),
        "word1_id": str(word1_id),
        "word2_id": str(word2_id),
    }


@pytest.mark.asyncio
async def test_get_all_term_pairs(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair_1 = TermPair(id=uuid4(), word1_id=uuid4(), word2_id=uuid4())
    term_pair_2 = TermPair(id=uuid4(), word1_id=uuid4(), word2_id=uuid4())

    def _mock_join_room():
        undercover_controller.get_term_pairs = AsyncMock(return_value=[term_pair_1, term_pair_2])
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get("/undercover/termpair")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(term_pair_1.id),
            "word1_id": str(term_pair_1.word1_id),
            "word2_id": str(term_pair_1.word2_id),
        },
        {
            "id": str(term_pair_2.id),
            "word1_id": str(term_pair_2.word1_id),
            "word2_id": str(term_pair_2.word2_id),
        },
    ]


@pytest.mark.asyncio
async def test_get_term_pair_by_id(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair_id = uuid4()
    term_pair = TermPair(id=term_pair_id, word1_id=uuid4(), word2_id=uuid4())

    def _mock_join_room():
        undercover_controller.get_term_pair_by_id = AsyncMock(return_value=term_pair)
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/termpair/{term_pair_id}")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(term_pair_id),
        "word1_id": str(term_pair.word1_id),
        "word2_id": str(term_pair.word2_id),
    }


@pytest.mark.asyncio
async def test_get_term_pair_by_id_not_found(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair_id = uuid4()

    def _mock_join_room():
        undercover_controller.get_term_pair_by_id = AsyncMock(
            side_effect=TermPairNotFoundError(term_pair_id=term_pair_id)
        )
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get(f"/undercover/termpair/{term_pair_id}")
    assert response.status_code == 404
    assert response.json() == {
        "name": "TermPairNotFoundError",
        "message": f"Term pair with id {term_pair_id} not found",
        "status_code": 404,
    }


@pytest.mark.asyncio
async def test_get_random_term_pair(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair = TermPair(id=uuid4(), word1_id=uuid4(), word2_id=uuid4())

    def _mock_join_room():
        undercover_controller.get_random_term_pair = AsyncMock(return_value=term_pair)
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get("/undercover/termpair/search/random")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(term_pair.id),
        "word1_id": str(term_pair.word1_id),
        "word2_id": str(term_pair.word2_id),
    }


@pytest.mark.asyncio
async def test_get_random_pair_not_found(
    undercover_controller: UndercoverController,
    faker: Faker,
    app: FastAPI,
    client: TestClient,
):

    term_pair_id = uuid4()

    def _mock_join_room():
        undercover_controller.get_random_term_pair = AsyncMock(
            side_effect=TermPairNotFoundError(term_pair_id=term_pair_id)
        )
        return undercover_controller

    app.dependency_overrides[get_undercover_controller] = _mock_join_room

    response = client.get("/undercover/termpair/search/random")
    assert response.status_code == 404
    assert response.json() == {
        "name": "TermPairNotFoundError",
        "message": f"Term pair with id {term_pair_id} not found",
        "status_code": 404,
    }
