import random
from typing import Sequence
from uuid import UUID

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlmodel import Session, select

from ibg.models.errors import (
    TermPairNotFoundError,
    WordNotFoundErrorId,
    WordAlreadyExistsError,
    WordNotFoundErrorName,
    TermPairAlreadyExistsError,
)
from ibg.models.undercover import Word, WordCreate, WordUpdate, TermPair


class UndercoverController:
    def __init__(self, session: Session):
        self.session = session

    async def create_word(self, word_create: WordCreate):
        try:
            new_word = Word(**word_create.model_dump())
            self.session.add(new_word)
            self.session.commit()
            self.session.refresh(new_word)
            return new_word
        except IntegrityError:
            raise WordAlreadyExistsError(word=word_create.word)

    async def get_words(self) -> Sequence[Word]:
        return self.session.exec(select(Word)).all()

    async def get_word_by_id(self, word_id: UUID) -> Word:
        """
        Get a word by its id. If the word does not exist, raise a NoResultFound exception.

        :param word_id: The id of the word to get.
        :type word_id: UUID
        :return: The word.
        :rtype: Word
        """
        try:
            return self.session.get_one(Word, word_id)
        except NoResultFound:
            raise WordNotFoundErrorId(word_id=word_id)

    async def get_word_by_word(self, word: str) -> Word:
        try:
            return self.session.exec(select(Word).where(Word.word == word)).one()
        except NoResultFound:
            raise WordNotFoundErrorName(word=word)

    async def delete_word(self, word_id: UUID) -> None:
        db_word = self.session.get_one(Word, word_id)
        self.session.delete(db_word)
        self.session.commit()

    async def update_word(self, word_id: UUID, word_update: WordUpdate) -> Word:
        try:
            db_word = self.session.get_one(Word, word_id)
        except NoResultFound:
            raise WordNotFoundErrorId(word_id=word_id)
        db_word_data = word_update.model_dump(exclude_unset=True)
        db_word.sqlmodel_update(db_word_data)
        self.session.add(db_word)
        self.session.commit()
        self.session.refresh(db_word)
        return db_word

    async def get_words_by_category(self, category: str) -> Sequence[Word]:
        return self.session.exec(select(Word).where(Word.category == category)).all()

    async def create_term_pair(self, word1_id: UUID, word2_id: UUID) -> TermPair:
        try:
            new_term_pair = TermPair(word1_id=word1_id, word2_id=word2_id)
            self.session.add(new_term_pair)
            self.session.commit()
            self.session.refresh(new_term_pair)
            return new_term_pair
        except IntegrityError:
            raise TermPairAlreadyExistsError(term1=str(word1_id), term2=str(word2_id))

    async def get_term_pairs(self) -> Sequence[TermPair]:
        return self.session.exec(select(TermPair)).all()

    async def get_term_pair_by_id(self, term_pair_id: UUID) -> TermPair:
        try:
            return self.session.exec(
                select(TermPair).where(TermPair.id == term_pair_id)
            ).one()
        except NoResultFound:
            raise TermPairNotFoundError(term_pair_id=term_pair_id)

    async def get_random_term_pair(self) -> TermPair:
        try:
            return random.choice(self.session.exec(select(TermPair)).all())
        except IndexError:
            raise NoResultFound

    async def delete_term_pair(self, term_pair_id: UUID) -> None:
        try:
            db_term_pair = self.session.exec(
                select(TermPair).where(TermPair.id == term_pair_id)
            ).one()
            self.session.delete(db_term_pair)
            self.session.commit()
        except NoResultFound:
            raise TermPairNotFoundError(term_pair_id=term_pair_id)
