import strawberry
from typing import Optional, TypeAlias

from fastapi import FastAPI
from sqlalchemy import select, DateTime
from datetime import datetime

from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from strawberry.dataloader import DataLoader

import models
from schemas import DocumentType
from schemas import Document
from schemas import AccountingEntry


@strawberry.type
class Author:
    id: strawberry.ID
    name: str
    nameUpper: str

    @strawberry.field
    async def books(self, info: Info) -> list["Book"]:
        books = await info.context["books_by_author"].load(self.id)
        return [Book.marshal(book) for book in books]

    @classmethod
    def marshal(cls, model: models.Author) -> "Author":
        return cls(id=strawberry.ID(str(model.id)), name=model.name, nameUpper=model.nameUpper())


@strawberry.type
class Book:
    id: strawberry.ID
    name: str
    author: Optional[Author] = None

    @classmethod
    def marshal(cls, model: models.Book) -> "Book":
        return cls(
            id=strawberry.ID(str(model.id)),
            name=model.name,
            author=Author.marshal(model.author) if model.author else None,
        )


@strawberry.type
class AuthorExists:
    message: str = "Author with this name already exist"


@strawberry.type
class AuthorNotFound:
    message: str = "Couldn't find an author with the supplied name"


@strawberry.type
class AuthorNameMissing:
    message: str = "Please supply an author name"


AddBookResponse = strawberry.union(
    "AddBookResponse", (Book, AuthorNotFound, AuthorNameMissing)
)
AddAuthorResponse = strawberry.union(
    "AddAuthorResponse", (Author, AuthorExists)
)


all_tasks: list = []


@strawberry.type
class Query:

    @strawberry.field
    async def accounting_entries(self) -> list[AccountingEntry]:
        async with models.get_session() as s:
            sql = select(models.AccountingEntry).order_by(
                models.AccountingEntry.name)
            db_accounting_entry = await s.execute(sql)
            data = db_accounting_entry.scalars().unique().all()

        return [AccountingEntry.marshal(entry) for entry in data]

    @strawberry.field
    async def books(self) -> list[Book]:
        async with models.get_session() as s:
            sql = select(models.Book).order_by(models.Book.name)
            db_book = (await s.execute(sql)).scalars().unique().all()
        return [Book.marshal(book) for book in db_book]

    @strawberry.field
    async def authors(self) -> list[Author]:
        async with models.get_session() as s:
            sql = select(models.Author).order_by(models.Author.name)
            db_authors = (await s.execute(sql)).scalars().unique().all()
        return [Author.marshal(loc) for loc in db_authors]


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def add_document(self, issuance: datetime, settlement: datetime, document_type_id: int, accounting_entry_id: Optional[int] = None) -> Document:
        async with models.get_session() as s:
            document_type = await s.get(models.DocumentType, document_type_id)
            accounting_entry = await s.get(models.AccountingEntry, accounting_entry_id) if accounting_entry_id else None

            new_document = models.Document(
                issuance=issuance, settlement=settlement, type=document_type, accounting_entry=accounting_entry)
            s.add(new_document)

            new_accounting_entry = models.AccountingEntry(
                name=f"{new_document.type.description}", document=new_document)
            s.add(new_accounting_entry)

            await s.commit()
            return Document.marshal(new_document)

    @strawberry.mutation
    async def add_document_type(self, description: str, afip_code: Optional[str] = None) -> DocumentType:
        async with models.get_session() as s:
            db_document_type = models.DocumentType(
                description=description, afip_code=afip_code)
            s.add(db_document_type)
            await s.commit()
        return DocumentType.marshal(db_document_type)

    @strawberry.mutation
    async def add_accounting_entry(self, id: str | None = None, name: str = "") -> AccountingEntry:
        async with models.get_session() as s:
            db_accounting_entry = models.AccountingEntry(id=id, name=name)
            s.add(db_accounting_entry)
            await s.commit()
        return AccountingEntry.marshal(db_accounting_entry)

    @strawberry.mutation
    async def add_book(self, name: str, author_name: Optional[str]) -> AddBookResponse:
        async with models.get_session() as s:
            db_author = None
            if author_name:
                sql = select(models.Author).where(
                    models.Author.name == author_name)
                db_author = (await s.execute(sql)).scalars().first()
                if not db_author:
                    return AuthorNotFound()
            else:
                return AuthorNameMissing()
            db_book = models.Book(name=name, author=db_author)
            s.add(db_book)
            await s.commit()
        return Book.marshal(db_book)

    @strawberry.mutation
    async def add_author(self, name: str) -> AddAuthorResponse:
        async with models.get_session() as s:
            sql = select(models.Author).where(models.Author.name == name)
            existing_db_author = (await s.execute(sql)).first()
            if existing_db_author is not None:
                return AuthorExists()
            db_author = models.Author(name=name)
            s.add(db_author)
            await s.commit()
        return Author.marshal(db_author)


async def load_books_by_author(keys: list) -> list[Book]:
    async with models.get_session() as s:
        all_queries = [select(models.Book).where(
            models.Book.author_id == key) for key in keys]
        data = [(await s.execute(sql)).scalars().unique().all() for sql in all_queries]
        print(keys, data)
    return data


async def load_author_by_book(keys: list) -> list[Book]:
    async with models.get_session() as s:
        sql = select(models.Author).where(models.Author.id in keys)
        data = (await s.execute(sql)).scalars().unique().all()
    if not data:
        data.append([])
    return data


async def get_context() -> dict:
    return {
        "author_by_book": DataLoader(load_fn=load_author_by_book),
        "books_by_author": DataLoader(load_fn=load_books_by_author),
    }

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
