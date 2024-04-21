import uvicorn


from ibg.api import create_app
from ibg.database import create_app_engine, create_db_and_tables

app = create_app()


@app.on_event("startup")
async def startup_event():
    engine = create_app_engine()
    create_db_and_tables(engine)
    engine.dispose()


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
