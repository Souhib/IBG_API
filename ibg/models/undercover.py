from uuid import UUID, uuid4

from pydantic import model_validator
from sqlmodel import Field

from ibg.models.shared import DBModel


class WordBase(DBModel):
    word: str = Field(index=True, unique=True)
    category: str
    short_description: str
    long_description: str


class Word(WordBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)


class WordCreate(WordBase):
    pass


class WordUpdate(WordBase):
    pass


class TermPairBase(DBModel):
    word1_id: UUID
    word2_id: UUID

    @model_validator(mode="after")
    def check_words_are_different(self) -> "TermPairBase":
        if self.word1_id and self.word2_id and self.word1_id == self.word2_id:
            raise ValueError("Words have to be different")
        return self


class TermPair(TermPairBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, unique=True)
    word1_id: UUID = Field(primary_key=True, foreign_key="word.id")
    word2_id: UUID = Field(primary_key=True, foreign_key="word.id")


class TermPairCreate(TermPairBase):
    pass
