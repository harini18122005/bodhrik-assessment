from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import SessionLocal, engine

# Alias for backwards compatibility
AsyncSessionLocal = SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection generator to yield db sessions and close them upon request completion."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
