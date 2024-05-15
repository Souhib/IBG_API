from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.exc import NoResultFound
from sqlmodel import select

from ibg.api.controllers.undercover import UndercoverController
from ibg.api.models.error import (
    TermPairAlreadyExistsError,
    TermPairNotFoundError,
    WordAlreadyExistsError,
    WordNotFoundErrorId,
    WordNotFoundErrorName,
)
from ibg.api.models.undercover import TermPair, Word, WordCreate, WordUpdate


@pytest.mark.asyncio
async def test_create_word(undercover_controller: UndercoverController, faker: Faker):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    word = await undercover_controller.create_word(word_create)
    assert word.word == word_create.word
    assert word.category == word_create.category
    assert word.short_description == word_create.short_description
    assert word.long_description == word_create.long_description


@pytest.mark.asyncio
async def test_create_word_raises_exception_if_word_already_exists(
    undercover_controller: UndercoverController, faker: Faker
):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    _ = await undercover_controller.create_word(word_create)
    with pytest.raises(WordAlreadyExistsError, match="Word .* already exists"):
        await undercover_controller.create_word(word_create)


@pytest.mark.asyncio
async def test_get_all_words(undercover_controller: UndercoverController, faker: Faker):
    words = []
    for _ in range(3):
        word_create = WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
        words.append(await undercover_controller.create_word(word_create))
    result = undercover_controller.session.exec(select(Word)).all()
    assert len(result) == 3
    for word, db_word in zip(words, result):
        assert word.word == db_word.word
        assert word.category == db_word.category
        assert word.short_description == db_word.short_description
        assert word.long_description == db_word.long_description


@pytest.mark.asyncio
async def test_get_word_by_id(undercover_controller: UndercoverController, faker: Faker):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    word = await undercover_controller.create_word(word_create)
    result = await undercover_controller.get_word_by_id(word.id)
    assert word.word == result.word
    assert word.category == result.category
    assert word.short_description == result.short_description
    assert word.long_description == result.long_description


@pytest.mark.asyncio
async def test_get_word_by_id_raises_exception_if_word_does_not_exist(
    undercover_controller: UndercoverController,
):
    with pytest.raises(WordNotFoundErrorId, match="Word with id .* not found"):
        await undercover_controller.get_word_by_id(uuid4())


@pytest.mark.asyncio
async def test_get_word_by_word(undercover_controller: UndercoverController, faker: Faker):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    word = await undercover_controller.create_word(word_create)
    result = await undercover_controller.get_word_by_word(word.word)
    assert word.word == result.word
    assert word.category == result.category
    assert word.short_description == result.short_description
    assert word.long_description == result.long_description


@pytest.mark.asyncio
async def test_get_word_by_word_raises_exception_if_word_does_not_exist(
    undercover_controller: UndercoverController, faker: Faker
):
    with pytest.raises(WordNotFoundErrorName, match="Word .* not found"):
        await undercover_controller.get_word_by_word(faker.word())


@pytest.mark.asyncio
async def test_delete_word(undercover_controller: UndercoverController, faker: Faker):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    word = await undercover_controller.create_word(word_create)
    await undercover_controller.delete_word(word.id)
    with pytest.raises(WordNotFoundErrorId, match="Word with id .* not found"):
        _ = await undercover_controller.get_word_by_id(word.id)


@pytest.mark.asyncio
async def test_delete_word_raises_exception_if_word_does_not_exist(
    undercover_controller: UndercoverController,
):
    with pytest.raises(NoResultFound):
        await undercover_controller.delete_word(uuid4())


@pytest.mark.asyncio
async def test_update_word(undercover_controller: UndercoverController, faker: Faker):
    word_create = WordCreate(
        word=faker.word(),
        category=faker.word(),
        short_description=faker.sentence(),
        long_description=faker.text(),
    )
    word = await undercover_controller.create_word(word_create)
    new_category = faker.word()
    updated_word = await undercover_controller.update_word(
        word.id,
        WordUpdate(
            word=word.word,
            category=new_category,
            short_description=word.short_description,
            long_description=word.long_description,
        ),
    )
    assert updated_word.word == word.word
    assert updated_word.category == new_category
    assert updated_word.short_description == word.short_description
    assert updated_word.long_description == word.long_description


@pytest.mark.asyncio
async def test_update_word_raises_exception_if_word_does_not_exist(
    undercover_controller: UndercoverController, faker: Faker
):
    with pytest.raises(WordNotFoundErrorId, match="Word with id .* not found"):
        await undercover_controller.update_word(
            uuid4(),
            WordUpdate(
                word=faker.word(),
                category=faker.word(),
                short_description=faker.sentence(),
                long_description=faker.text(),
            ),
        )


@pytest.mark.asyncio
async def test_get_words_by_category(undercover_controller: UndercoverController, faker: Faker):
    words = []
    category_one = faker.word()
    category_two = faker.word()
    for _ in range(2):
        word_create = WordCreate(
            word=faker.word(),
            category=category_one,
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
        words.append(await undercover_controller.create_word(word_create))
    _ = [
        await undercover_controller.create_word(
            WordCreate(
                word=faker.word(),
                category=category_two,
                short_description=faker.sentence(),
                long_description=faker.text(),
            )
        )
        for _ in range(2)
    ]
    result = await undercover_controller.get_words_by_category(category_one)
    assert len(result) == 2
    assert words[0].word == result[0].word
    assert words[0].category == result[0].category
    assert words[0].short_description == result[0].short_description
    assert words[0].long_description == result[0].long_description
    assert words[1].word == result[1].word
    assert words[1].category == result[1].category
    assert words[1].short_description == result[1].short_description
    assert words[1].long_description == result[1].long_description


@pytest.mark.asyncio
async def test_create_term_pair(undercover_controller: UndercoverController, faker: Faker):
    word1 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    word2 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )

    term_pair = await undercover_controller.create_term_pair(word1.id, word2.id)
    assert term_pair.word1_id == word1.id
    assert term_pair.word2_id == word2.id


@pytest.mark.asyncio
async def test_create_term_pair_raises_exception_if_term_pair_already_exists(
    undercover_controller: UndercoverController, faker: Faker
):
    word1 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    word2 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    _ = await undercover_controller.create_term_pair(word1.id, word2.id)
    with pytest.raises(TermPairAlreadyExistsError, match="Term pair .* - .* already exists"):
        await undercover_controller.create_term_pair(word1.id, word2.id)


@pytest.mark.asyncio
async def test_get_all_term_pairs(undercover_controller: UndercoverController, faker: Faker):
    term_pairs = []
    for _ in range(3):
        word1 = await undercover_controller.create_word(
            WordCreate(
                word=faker.word(),
                category=faker.word(),
                short_description=faker.sentence(),
                long_description=faker.text(),
            )
        )
        word2 = await undercover_controller.create_word(
            WordCreate(
                word=faker.word(),
                category=faker.word(),
                short_description=faker.sentence(),
                long_description=faker.text(),
            )
        )
        term_pairs.append(await undercover_controller.create_term_pair(word1.id, word2.id))
    result = undercover_controller.session.exec(select(TermPair)).all()
    assert len(result) == 3
    for term_pair, db_term_pair in zip(term_pairs, result):
        assert term_pair.word1_id == db_term_pair.word1_id
        assert term_pair.word2_id == db_term_pair.word2_id


@pytest.mark.asyncio
async def test_get_term_pair_by_id(undercover_controller: UndercoverController, faker: Faker):
    word1 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    word2 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    term_pair = await undercover_controller.create_term_pair(word1.id, word2.id)
    result = await undercover_controller.get_term_pair_by_id(term_pair.id)
    assert term_pair.word1_id == result.word1_id
    assert term_pair.word2_id == result.word2_id


@pytest.mark.asyncio
async def test_get_term_pair_by_id_raises_exception_if_term_pair_does_not_exist(
    undercover_controller: UndercoverController,
):
    with pytest.raises(TermPairNotFoundError, match="Term pair with id .* not found"):
        await undercover_controller.get_term_pair_by_id(uuid4())


@pytest.mark.asyncio
async def test_get_random_term_pair(undercover_controller: UndercoverController, faker: Faker):
    term_pairs = []
    for _ in range(3):
        word1 = await undercover_controller.create_word(
            WordCreate(
                word=faker.word(),
                category=faker.word(),
                short_description=faker.sentence(),
                long_description=faker.text(),
            )
        )
        word2 = await undercover_controller.create_word(
            WordCreate(
                word=faker.word(),
                category=faker.word(),
                short_description=faker.sentence(),
                long_description=faker.text(),
            )
        )
        term_pairs.append(await undercover_controller.create_term_pair(word1.id, word2.id))
    result = await undercover_controller.get_random_term_pair()
    assert result in term_pairs


@pytest.mark.asyncio
async def test_get_random_term_pair_raises_exception_if_no_term_pairs_exist(
    undercover_controller: UndercoverController,
):
    with pytest.raises(NoResultFound):
        await undercover_controller.get_random_term_pair()


@pytest.mark.asyncio
async def test_delete_term_pair(undercover_controller: UndercoverController, faker: Faker):
    word1 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    word2 = await undercover_controller.create_word(
        WordCreate(
            word=faker.word(),
            category=faker.word(),
            short_description=faker.sentence(),
            long_description=faker.text(),
        )
    )
    term_pair = await undercover_controller.create_term_pair(word1.id, word2.id)
    await undercover_controller.delete_term_pair(term_pair.id)
    with pytest.raises(TermPairNotFoundError):
        _ = await undercover_controller.get_term_pair_by_id(term_pair.id)


@pytest.mark.asyncio
async def test_delete_term_pair_raises_exception_if_term_pair_does_not_exist(
    undercover_controller: UndercoverController,
):
    with pytest.raises(TermPairNotFoundError):
        await undercover_controller.delete_term_pair(uuid4())
