import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

# Update with your actual database URL
sqlite_file_name = "test.db"
sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"


async def reset_database():
    # Create Async Engine
    engine: AsyncEngine = create_async_engine(sqlite_url, echo=True)

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("All tables dropped.")

    # Recreate all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("All tables recreated.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_database())
