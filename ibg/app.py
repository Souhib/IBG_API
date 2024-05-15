import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy.exc import NoResultFound
from starlette.responses import JSONResponse

from ibg.api.models.error import BaseError
from ibg.api.routers.game import router as game_router
from ibg.api.routers.room import router as room_router
from ibg.api.routers.undercover import router as undercover_router
from ibg.api.routers.user import router as user_router
from ibg.socketio.models.shared import IBGSocket
from ibg.socketio.routers import room, undercover
from ibg.socketio.routers.room import router as socket_router


def create_socket_io_app() -> socketio.ASGIApp:
    """
    It creates a socket.io app and adds the events we created earlier
    :return: A socket.io app
    """
    sio = IBGSocket()
    socketio_app = socketio.ASGIApp(sio)
    room.room_events(sio)
    undercover.undercover_events(sio)
    return socketio_app


def create_app(lifespan) -> FastAPI:
    """
    It creates a FastAPI app, adds CORS middleware, and includes the routers we created earlier

    :return: A FastAPI object
    """
    origins = ["*"]
    app = FastAPI(title="IBG", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_router)
    app.include_router(room_router)
    app.include_router(game_router)
    app.include_router(undercover_router)
    app.include_router(socket_router)
    # logfire.configure(
    #     send_to_logfire=True,
    #     project_name="ibg-api",
    #     token="",
    #     pydantic_plugin=logfire.PydanticPlugin(record="all"),
    # )
    # logfire.instrument_fastapi(app)
    socketio_app = create_socket_io_app()
    app.mount("/", socketio_app)

    @app.get("/scalar", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(
            openapi_url="/openapi.json",
            title="IBG API Scalar",
        )

    @app.exception_handler(NoResultFound)
    async def no_result_found_exception_handler(request: Request, exc: NoResultFound):
        return JSONResponse(
            status_code=404,
            content={"message": "Couldn't find requested resource"},
        )

    @app.exception_handler(BaseError)
    async def base_error_exception_handler(request: Request, exc: BaseError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "name": exc.name,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    return app
