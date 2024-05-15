from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, ValidationError

from ibg.api.models.error import BaseError
from ibg.socketio.models.shared import IBGSocket


def serialize_model(data: Any) -> Any:
    """
    Recursively convert a Pydantic model and any nested UUIDs to a dictionary with stringified UUIDs.
    Handles lists, dicts, and Pydantic models. Converts UUIDs to strings.
    """
    if isinstance(data, BaseModel):
        return {key: serialize_model(value) for key, value in data.model_dump().items()}
    elif isinstance(data, UUID):
        return str(data)
    elif isinstance(data, dict):
        return {key: serialize_model(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_model(item) for item in data]
    elif isinstance(data, datetime):
        return data.strftime("%Y-%m-%d %H:%M:%S")
    return data


async def send_event_to_client(sio: IBGSocket, event_name: str, data: dict[str, Any], room: str) -> None:
    await sio.emit(event_name, data, room=room)


def socketio_exception_handler(sio):
    def decorator(func):
        @wraps(func)
        async def wrapper(sid, *args, **kwargs):
            try:
                return await func(sid, *args, **kwargs)
            except BaseError as e:
                path = Path(e.__traceback__.tb_frame.f_code.co_filename)
                filename = path.name
                parent_dir = path.parent.name
                grand_parent_folder = path.parent.parent.name
                await sio.emit(
                    "error",
                    {
                        "name": type(e).__name__,
                        "message": str(e),
                        "status_code": e.status_code,
                        "exc_info": f"{grand_parent_folder}/{parent_dir}/{filename}:{e.__traceback__.tb_lineno}",
                    },
                    room=sid,
                )
                logger.exception(f"Error: {e}")
            except ValidationError as e:
                errors = e.errors()
                error_messages = str({error["loc"][0]: error["msg"] for error in errors})
                path = Path(e.__traceback__.tb_frame.f_code.co_filename)
                filename = path.name
                parent_dir = path.parent.name
                grand_parent_folder = path.parent.parent.name
                logger.info(
                    {
                        "name": e.__class__.__name__,
                        "message": error_messages,
                        "status_code": 422,
                        "exc_info": f"{grand_parent_folder}/{parent_dir}/{filename}:{e.__traceback__.tb_lineno}",
                    }
                )
                logger.exception(f"Error: {e}")
                await sio.emit(
                    "error",
                    {
                        "name": e.__class__.__name__,
                        "message": error_messages,
                        "status_code": 422,
                    },
                    room=sid,
                )
            except Exception as e:
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                path = Path(e.__traceback__.tb_frame.f_code.co_filename)
                filename = path.name
                parent_dir = path.parent.name
                grand_parent_folder = path.parent.parent.name
                logger.critical(
                    {
                        "name": type(e).__name__,
                        "message": repr(e),
                        "datetime": date,
                        "status_code": 500,
                        "exc_info": f"{grand_parent_folder}/{parent_dir}/{filename}:{e.__traceback__.tb_lineno}",
                    }
                )
                logger.exception(f"Error: {e}")
                await sio.emit(
                    "error",
                    {"name": type(e).__name__, "message": repr(e), "status_code": 500},
                    room=sid,
                )

        return wrapper

    return decorator
