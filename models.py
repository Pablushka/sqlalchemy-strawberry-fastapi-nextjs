# models.py define la estructura física de la base de datos

from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship, sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy_mysql_binary_uuid import BinaryUUID
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from uuid import uuid4
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncio


# Base = declarative_base()
class Base(DeclarativeBase):
    pass


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # date_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    # date_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    books: Mapped[list["Book"]] = relationship(
        "Book", lazy="joined", back_populates="author")

    def nameUpper(self) -> str:
        return self.name.upper()


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    author_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(Author.id), nullable=True)

    author: Mapped[Optional[Author]] = relationship(
        Author, lazy="joined", back_populates="books")


engine = create_async_engine(
    # "sqlite+aiosqlite:///./database.db", connect_args={"check_same_thread": False}
    "mysql+aiomysql://root:secreto!@127.0.0.1:3306/test?charset=utf8mb4"

)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            finally:
                await session.close()


async def _async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    print("Dropping and creating tables")
    asyncio.run(_async_main())
    print("Done.")
