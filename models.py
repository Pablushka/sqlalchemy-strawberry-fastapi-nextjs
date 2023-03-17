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
    id = mapped_column(Integer, primary_key=True, index=True)
    description = mapped_column(String(100), nullable=False)
    afip_code = mapped_column(String(3), nullable=True)
    
    document_type_relation = relationship(
        "Document", lazy="joined", back_populates="type_id_relation")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    issuance: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True)

    settlement: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True)

    
    accounting_entry_id: Mapped[int] = mapped_column(
        BinaryUUID, ForeignKey("accounting_entries.id"), nullable=True, index=True)

    accounting_entry_relation: Mapped[Optional["AccountingEntry"]] = relationship(
       lazy="joined", back_populates="document_relation")

    
    operation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("operations.id"), nullable=False, index=True)
    
    operation_relation = relationship(
        "Operation", lazy="joined", back_populates="document_relation")

    
    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_types.id"), nullable=True)  # tipo de comprobante

    type_id_relation = relationship(
        "DocumentType", lazy="joined", back_populates="document_type_relation")

    
    document_payment_relation = relationship("TaxPayment", back_populates="document_tax_payment_relation")


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    # commitent_id: Mapped[Optional[int]] = mapped_column(

    document_id: Mapped[Optional[int]] = mapped_column(
        BinaryUUID, ForeignKey("documents.id"), nullable=True, index=True)

    document_relation: Mapped[Optional[Document]] = relationship(
        uselist=False, lazy="joined", back_populates="accounting_entry_relation")

       
    
    created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())
    

    accounting_entry_detail_relation = relationship(
        "AccountingEntryDetail", lazy="joined", back_populates="accounting_entry_relation")
    

class AccountingEntryDetail(Base):
    __tablename__ = "accounting_entries_details"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    # fk a la cuenta del plan de cuentas
    amount = mapped_column(DECIMAL(18, 2), nullable=False)
    column = mapped_column(String(1), nullable=False) #Debe o Haber

   
    accounting_entry_id: Mapped[Optional[int]] = mapped_column(
        BinaryUUID, ForeignKey("accounting_entries.id"), nullable=False, index=True)

    accounting_entry_relation: Mapped[Optional[AccountingEntry]] = relationship(
        "AccountingEntry", lazy="joined", back_populates="accounting_entry_detail_relation")
    

    created = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
       
    
    liquidation_entries_relation = relationship(
        "LiquidationEntry",  lazy="joined", back_populates="accounting_entry_detail_relation")




class Operation(Base):
    __tablename__ = "operations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    
    document_id: Mapped[int] = mapped_column(
        BinaryUUID, ForeignKey("documents.id"), nullable=False, index=True)
   
    document_relation = relationship(
        "Document", lazy="joined", back_populates="operation_relation")
    

class LiquidationEntry(Base):
    __tablename__ = "liquidation_entries"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)

    
    neto_iva: Mapped[bool] = mapped_column(Boolean, nullable=False)
    neto_iibb: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    state_id = mapped_column(
        Integer, ForeignKey("states.id"), nullable=False, index=True)
    
    state_id_relation = relationship(
        "State",lazy="joined", back_populates="liquidation_entry_state_relation")

    
    accounting_entry_detail_id: Mapped[int] = mapped_column(
        BinaryUUID, ForeignKey("accounting_entries_details.id"), nullable=True, index=True)

    accounting_entry_detail_relation: Mapped[Optional[AccountingEntryDetail]] = relationship(
        lazy="joined", back_populates="liquidation_entries_relation")


    aliquots_iva_id = mapped_column(
        Integer, ForeignKey("aliquots_iva.id"), nullable=False, index=True)
    
    aliquots_iva_id_relation = relationship( 
        "AliquotsIVA", back_populates= "liquidation_aliquots_iva_relation"
    )

    
    activity_id = mapped_column(
        Integer, ForeignKey("activities.id"), nullable=False, index=True)
    
    activity_id_relation = relationship( 
        "Activity", back_populates= "liquidation_activity_relation"
    )

    tax_credit_option_id = mapped_column(
        Integer, ForeignKey("tax_credit_options.id"), nullable=True, index=True)

    tax_credit_option_relation = relationship("TaxCreditOption", lazy="joined",
                           back_populates="tax_credit_option_liquidation_relation")

    created = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class State(Base):
    __tablename__ = "states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    afip_code: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(50), nullable=False)

    liquidation_entry_state_relation = relationship(
        "LiquidationEntry",lazy="joined", back_populates="state_id_relation")
    
    state_tax_payment_relation = relationship("TaxPayment", back_populates="state_relation")


class AliquotsIVA(Base):
    __tablename__ = "aliquots_iva"
    id = mapped_column(Integer, primary_key=True, index=True)
    description = mapped_column(String(50), nullable=False)
    percentage = mapped_column(
        DECIMAL(4, 3), nullable=False)  # 0.001 - 9.999
    
    liquidation_aliquots_iva_relation = relationship( 
        "LiquidationEntry", back_populates= "aliquots_iva_id_relation"
    )


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    afip_code: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(50), nullable=False)

    liquidation_activity_relation = relationship("LiquidationEntry", back_populates="activity_id_relation" )


class TaxCreditOption(Base):
    __tablename__ = "tax_credit_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(50), nullable=False)

    tax_credit_option_liquidation_relation = relationship("LiquidationEntry", back_populates="tax_credit_option_relation")

class Tax(Base):
    __tablename__="taxes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    afip_code: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)

    tax_payment_relation = relationship("TaxPayment", back_populates="tax_relation")

class TaxPaymentType(Base):
    __tablename__="tax_payment_types"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(20), nullable=False)

   
    payment_type_relation = relationship("TaxPayment", back_populates="type_tax_payment_relation")


class TaxPayment(Base):
    __tablename__="tax_payments"
    id: Mapped[int] = mapped_column(
        BinaryUUID, primary_key=True, default=uuid4)
    emitter_cuit = mapped_column(Integer, nullable=False)
    sender_cuit = mapped_column(Integer, nullable=False)
    issuance:Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    trigger_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    certificate = mapped_column(Integer, nullable=False)


    tax_id= mapped_column(Integer, ForeignKey("taxes.id"), nullable=False)
    tax_relation = relationship("Tax", back_populates="tax_payment_relation")


    document_id: Mapped[int] = mapped_column(BinaryUUID, ForeignKey("documents.id"), nullable=True)
    document_tax_payment_relation = relationship("Document", back_populates="document_payment_relation")

    state_id = mapped_column(
        Integer, ForeignKey("states.id"), nullable=True, index=True) #nullable True porque puede ser una retención nacional  
    state_relation = relationship("State", back_populates="state_tax_payment_relation")
    
    type_tax_payment = mapped_column(
        Integer, ForeignKey("tax_payment_types.id"), nullable=False) 
    type_tax_payment_relation = relationship("TaxPaymentType", back_populates="payment_type_relation")
    
    

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
