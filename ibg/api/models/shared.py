from pydantic import ConfigDict
from sqlmodel import SQLModel


class DBModel(SQLModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)  # type: ignore


class LazyControllerLoader:
    def __init__(self, factory):
        self.factory = factory
        self.controller = None

    def __get__(self, obj, objtype=None):
        if self.controller is None:
            self.controller = self.factory()
        return self.controller
