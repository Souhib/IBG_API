import secrets
import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password. Return True if the password is correct, False otherwise.

    :param plain_password: The plain password to verify.
    :param hashed_password: The hashed password to verify against.
    :return: True if the password is correct, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get the hash of a password.

    :param password: The password to hash.
    :return: The hashed password.
    """
    return pwd_context.hash(password)


def create_random_string() -> str:
    """
    Create a random string of 16 characters, including letters, numbers, and punctuation.

    :return: A random string of 16 characters.
    """
    return "".join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))


def create_random_public_id() -> str:
    """
    Create a random public id of 4 characters, including letters and numbers.

    :return: A random public id of 4 characters.
    """
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(5))


def generate_password() -> str:
    """
    It generates a random hashed password.

    :return: A hashed string of 16 characters, including letters, numbers, and punctuation.
    """
    return get_password_hash(create_random_string())
