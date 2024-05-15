from uuid import UUID


class BaseError(Exception):
    def __init__(self, name: str, message: str, status_code: int):
        self.name = name
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotInRoomError(BaseError):
    def __init__(
        self,
        user_id: UUID,
        room_id: UUID,
        status_code: int = 404,
        name: str = "UserNotInRoomError",
    ):
        self.name = name
        self.message = f"User with id {user_id} is not in room with id {room_id}"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class WrongRoomPasswordError(BaseError):
    def __init__(
        self,
        room_id: UUID,
        status_code: int = 403,
        name: str = "WrongRoomPasswordError",
    ):
        self.name = name
        self.message = f"The password to join the room with id : {room_id} is incorrect"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class ErrorRoomIsNotActive(BaseError):
    def __init__(self, room_id: UUID, status_code: int = 403, name: str = "ErrorRoomIsNotActive"):
        self.name = name
        self.message = f"Room with id {room_id} is not active"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class UserAlreadyExistsError(BaseError):
    def __init__(
        self,
        email_address: str,
        status_code: int = 409,
        name: str = "UserAlreadyExistsError",
    ):
        self.name = name
        self.message = f"User with email address {email_address} already exists"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class UserNotFoundError(BaseError):
    def __init__(self, user_id: UUID, status_code: int = 404, name: str = "UserNotFoundError"):
        self.name = name
        self.message = f"User with id {user_id} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class RoomNotFoundError(BaseError):
    def __init__(
        self,
        room_id: UUID | str,
        status_code: int = 404,
        name: str = "RoomNotFoundError",
    ):
        self.name = name
        self.message = f"Room with id {room_id} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class GameNotFoundError(BaseError):
    def __init__(
        self,
        game_id: UUID | str,
        status_code: int = 404,
        name: str = "GameNotFoundError",
    ):
        self.name = name
        self.message = f"Game with id {game_id} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class UserAlreadyInRoomError(BaseError):
    def __init__(
        self,
        user_id: UUID | str,
        room_id: UUID | str,
        status_code: int = 409,
        name: str = "UserAlreadyInRoomError",
    ):
        self.name = name
        self.message = f"User with id {user_id} is already in room with id {room_id}"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class WordAlreadyExistsError(BaseError):
    def __init__(
        self,
        word: str,
        status_code: int = 409,
        name: str = "WordAlreadyExistsError",
    ):
        self.name = name
        self.message = f"Word {word} already exists"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class WordNotFoundErrorId(BaseError):
    def __init__(self, word_id: UUID, status_code: int = 404, name: str = "WordNotFoundError"):
        self.name = name
        self.message = f"Word with id {word_id} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class WordNotFoundErrorName(BaseError):
    def __init__(self, word: str, status_code: int = 404, name: str = "WordNotFoundError"):
        self.name = name
        self.message = f"Word {word} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class TermPairAlreadyExistsError(BaseError):
    def __init__(
        self,
        term1: str,
        term2: str,
        status_code: int = 409,
        name: str = "TermPairAlreadyExistsError",
    ):
        self.name = name
        self.message = f"Term pair {term1} - {term2} already exists"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class TermPairNotFoundError(BaseError):
    def __init__(
        self,
        term_pair_id: UUID,
        status_code: int = 404,
        name: str = "TermPairNotFoundError",
    ):
        self.name = name
        self.message = f"Term pair with id {term_pair_id} not found"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class NoTurnInsideGameError(BaseError):
    def __init__(
        self,
        game_id: UUID | str,
        status_code: int = 404,
        name: str = "NoTurnInsideGameError",
    ):
        self.name = name
        self.message = f"No turn inside game with id {game_id}"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class CantVoteBecauseYouDeadError(BaseError):
    def __init__(
        self,
        user_id: UUID | str,
        status_code: int = 403,
        name: str = "CantVoteBecauseYoureDeadError",
    ):
        self.name = name
        self.message = f"User with id {user_id} can't vote because they're dead"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class CantVoteForYourselfError(BaseError):
    def __init__(
        self,
        user_id: UUID | str,
        status_code: int = 403,
        name: str = "CantVoteForYourselfError",
    ):
        self.name = name
        self.message = f"User with id {user_id} can't vote for himself/herself"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class CantVoteForDeadPersonError(BaseError):
    def __init__(
        self,
        user_id: UUID | str,
        dead_user_id: UUID | str,
        status_code: int = 403,
        name: str = "CantVoteForDeadPersonError",
    ):
        self.name = name
        self.message = f"User with id {user_id} can't vote for dead user with id {dead_user_id}"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)


class RoomAlreadyExistsError(BaseError):
    def __init__(
        self,
        room_id: UUID | str,
        status_code: int = 409,
        name: str = "RoomAlreadyExistsError",
    ):
        self.name = name
        self.message = f"Room with id {room_id} already exists"
        self.status_code = status_code
        super().__init__(name=self.name, message=self.message, status_code=self.status_code)
