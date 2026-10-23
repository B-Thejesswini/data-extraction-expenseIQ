import asyncio

from sqlalchemy import text

from data_extraction_project.db.postgres_db import engine


async def main() -> None:
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version()"))).scalar_one()
        print("Connected OK:", version)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
