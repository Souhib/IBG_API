from typing import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session, select

from ibg.models.errors import UserAlreadyExistsError, UserNotFoundError
from ibg.models.user import UserCreate, UserUpdate
from ibg.models.models import User


class UserController:
    def __init__(self, session: Session):
        self.session = session

    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user in the database and return the created user.

        :param user_create: The body of the user we have to create.
        :return: The created user.
        """
        try:
            new_user = User(**user_create.model_dump())
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
            return new_user
        except IntegrityError:
            raise UserAlreadyExistsError(email_address=user_create.email_address)

    async def get_users(self) -> Sequence[User]:
        """
        Get all users from the database.
        :return: A list of all users in the database.
        """
        return self.session.exec(select(User)).all()

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get a user from the database by id. If the user does not exist, raise a NoResultFound exception.
        :param user_id: The id of the user to get.
        :return: The user with the given id.
        """
        try:
            return self.session.get_one(User, user_id)
        except NoResultFound:
            raise UserNotFoundError(user_id=user_id)

    async def update_user_by_id(self, user_id: UUID, user_update: UserUpdate) -> User:
        """
        Update a user in the database by id. If the user does not exist it raises an NoResultFound exception.
        :param user_id: The id of the user to update.
        :param user_update: The parameters we want to update.
        :return: The updated user.
        """
        try:
            db_user = self.session.get_one(User, user_id)
            db_user_data = user_update.model_dump(exclude_unset=True)
            db_user.sqlmodel_update(db_user_data)
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            return db_user
        except NoResultFound:
            raise UserNotFoundError(user_id=user_id)

    async def delete_user(self, user_id: UUID) -> None:
        """
        Delete a user from the database by id. If the user does not exist it raises an NoResultFound exception.
        :param user_id: The id of the user to delete.
        :return: None
        """
        try:
            db_user = self.session.get_one(User, user_id)
            self.session.delete(db_user)
            self.session.commit()
        except NoResultFound:
            raise UserNotFoundError(user_id=user_id)

    async def update_user_password(self, user_id: UUID, password: str) -> User:
        """
        Update the password of a user in the database by id. If the user does not exist it raises an NoResultFound exception.
        :param user_id: The id of the user to update.
        :param password: The new password of the user.
        :return: The updated user.
        """
        try:
            db_user = self.session.get_one(User, user_id)
            db_user.password = password
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            return db_user
        except NoResultFound:
            raise UserNotFoundError(user_id=user_id)
