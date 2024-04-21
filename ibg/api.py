from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import NoResultFound
from starlette.responses import JSONResponse

from ibg.models.errors import BaseError
from ibg.routers.user import router as user_router
from ibg.routers.game import router as game_router
from ibg.routers.undercover import router as undercover_router
from ibg.routers.socket import router as socket_router
from ibg.routers.room import router as room_router


def create_app() -> FastAPI:
    """
    It creates a FastAPI app, adds CORS middleware, and includes the routers we created earlier

    :return: A FastAPI object
    """
    origins = ["*"]
    app = FastAPI(title="IBG")
    app.add_middleware(
        CORSMiddleware,
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
