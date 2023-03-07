# models.py define la estructura física de la base de datos

from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy_mysql_binary_uuid import BinaryUUID
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, DECIMAL, Boolean, func
from uuid import uuid4
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncio
import logging
from decimal import Decimal


logger = logging.getLogger(__name__)

# Base = declarative_base()


class Base(DeclarativeBase):
    pass


class DocumentType(Base):
    __tablename__ = "document_types"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    afip_code: Mapped[str] = mapped_column(String(3), nullable=True)
    # documents: Mapped[list["Document"]] = relationship(
    #     "Document", lazy="joined", back_populates="type")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    issuance: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True)

    settlement: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True)

    accounting_entry_id: Mapped[int] = mapped_column(
        BinaryUUID, ForeignKey("accounting_entries.id"), nullable=True, index=True, name="fk_document_accounting_entry_id")

    accounting_entry: Mapped[Optional["AccountingEntry"]] = relationship(
        "AccountingEntry", lazy="joined", back_populates="document")

    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey(DocumentType.id), nullable=True, name="fk_document_type_id")  # tipo de comprobante

    type: Mapped[DocumentType] = relationship(
        DocumentType, lazy="joined")  # , back_populates="documents"

    operation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("operations.id"), nullable=False, index=True, name="fk_document_operation_id")


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    # commitent_id: Mapped[Optional[int]] = mapped_column(

    document_id: Mapped[Optional[int]] = mapped_column(
        BinaryUUID, ForeignKey(Document.id), nullable=True, index=True, name="fk_accounting_entry_document_id")

    document: Mapped[Optional[Document]] = relationship(
        Document, uselist=False, lazy="joined", back_populates="accounting_entry")

    details: Mapped[list["AccountingEntryDetail"]] = relationship(
        "AccountingEntryDetail", lazy="joined", back_populates="accounting_entry")

    created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())


class AccountingEntryDetail(Base):
    __tablename__ = "accounting_entries_details"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    # fk a la cuenta del plan de cuentas
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    column: Mapped[str] = mapped_column(String(1), nullable=False)

    accounting_entry_id: Mapped[Optional[int]] = mapped_column(
        BinaryUUID, ForeignKey(AccountingEntry.id), nullable=True, index=True)

    liquidation_entries_id: Mapped[Optional[int]] = mapped_column(
        BinaryUUID, ForeignKey("liquidation_entries.id"), nullable=True, index=True, name="fk_accounting_entry_detail_liquidation_entry_id")

    # accounting_entry: Mapped[Optional[AccountingEntry]] = relationship(
    #     AccountingEntry, lazy="joined", back_populates="details")

    created = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Operation(Base):
    __tablename__ = "operations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)

    # sells: Mapped[list["Document"]] = relationship(
    #     Document, lazy="joined", back_populates="operation")

    # filter sells relation by type_id = 1
    # TODO: Experimentar filtro por tipo de operacion
    sells = relationship(
        Document, lazy="joined", back_populates="operation", foreign_keys=[Document.id], primaryjoin="and_(Document.id==1, Document.operation_id==Operation.id)")


class LiquidationEntry(Base):
    __tablename__ = "liquidation_entries"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    # commitent_id: Mapped[Optional[int]] = mapped_column(

    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("states.id"), nullable=False, index=True, name="fk_liquidation_entry_state_id")

    accounting_entry_detail_id: Mapped[int] = mapped_column(
        BinaryUUID, ForeignKey(AccountingEntryDetail.id), nullable=True, index=True, name="fk_liquidation_entry_accounting_entry_detail_id")

    accounting_entry_detail: Mapped[Optional[AccountingEntryDetail]] = relationship(
        AccountingEntryDetail, lazy="joined", back_populates="liquidation_entries")

    neto_iva: Mapped[bool] = mapped_column(Boolean, nullable=False)
    neto_iibb: Mapped[bool] = mapped_column(Boolean, nullable=False)

    aliquots_iva_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("aliquots_iva.id"), nullable=False, index=True, name="fk_liquidation_entry_aliquots_iva_id")

    activity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("activities.id"), nullable=False, index=True, name="fk_liquidation_entry_activity_id")

    tax_credit_option_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tax_credit_options.id"), nullable=True, index=True, name="fk_liquidation_entry_tax_credit_option_id")

    details = relationship("AccountingEntryDetail", lazy="joined",
                           back_populates="accounting_entry")

    created = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class State(Base):
    __tablename__ = "states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    afip_code: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(50), nullable=False)


class AliquotsIVA(Base):
    __tablename__ = "aliquots_iva"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(50), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 3), nullable=False)  # 0.001 - 9.999


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    afip_code: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(50), nullable=False)


class TaxCreditOption(Base):
    __tablename__ = "tax_credit_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(50), nullable=False)


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
    "mysql+aiomysql://root:secreto!@127.0.0.1:3306/test?charset=utf8mb4",
    echo=True

)

async_session = async_sessionmaker(
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
            except SQLAlchemyError as e:
                logger.exception(e)
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
