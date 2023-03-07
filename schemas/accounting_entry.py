from .document import Document
from models import AccountingEntry as AccountingEntryModel
from typing import Optional
import strawberry
from datetime import datetime


@strawberry.type
class AccountingEntry:
    id: strawberry.ID
    name: str
    created: datetime
    document: Optional['Document'] = None
    updated: Optional[datetime] = None

    @classmethod
    def marshal(cls, model: AccountingEntryModel) -> 'AccountingEntry':
        return cls(id=strawberry.ID(str(model.id)), name=model.name, document=model.document, created=model.created, updated=model.updated)
