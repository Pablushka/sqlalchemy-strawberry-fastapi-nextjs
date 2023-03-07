
import strawberry
from models import Document as DocumentModel
from typing import Optional
from .document_type import DocumentType

from datetime import datetime


@strawberry.type
class Document:
    id: strawberry.ID
    issuance: datetime
    settlement: datetime
    type: DocumentType
    accounting_entry: Optional['AccountingEntry'] = None

    @classmethod
    def marshal(cls, model: DocumentModel) -> "Document":
        return cls(
            id=strawberry.ID(str(model.id)),

            # convert mode.issuance to datetime
            issuance=model.issuance,  # type: ignore
            settlement=model.settlement,  # type: ignore
            accounting_entry=AccountingEntry.marshal(
                model.accounting_entry) if model.accounting_entry else None,
            type=DocumentType.marshal(model.type)
        )


from .accounting_entry import AccountingEntry
