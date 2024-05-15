from uuid import uuid4

import pytest
from faker import Faker

from ibg.api.models.undercover import TermPair, Word


def test_create_word_with_all_required_fields(faker: Faker):
    # Arrange
    word = faker.word()
    category = faker.word()
    short_description = faker.sentence()
    long_description = faker.paragraph()

    # Act
    new_word = Word(
        word=word,
        category=category,
        short_description=short_description,
        long_description=long_description,
    )

    # Assert
    assert new_word.word == word
    assert new_word.category == category
    assert new_word.short_description == short_description
    assert new_word.long_description == long_description


def test_check_words_are_different_raises_error_when_words_are_same():
    # Arrange
    uuid = uuid4()

    # Act & Assert
    with pytest.raises(ValueError, match="Words have to be different"):
        _ = TermPair(word1_id=uuid, word2_id=uuid)
