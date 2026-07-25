"""PostgreSQL database configuration, SQLAlchemy engine, and session setup."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create the SQLAlchemy Async Engine using the DATABASE_URL environment variable.
# pool_pre_ping=True prevents database connection dropouts in production.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Create SessionLocal async sessionmaker for handling asynchronous DB connections.
# expire_on_commit=False ensures objects remain accessible after commit.
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Define the Declarative Base class that all database models will inherit from.
class Base(DeclarativeBase):
    pass
