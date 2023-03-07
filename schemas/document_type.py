from models import DocumentType as DocumentTypeModel

import strawberry


@strawberry.type
class DocumentType:
    id: strawberry.ID
    description: str
    afip_code: str | None = None

    @classmethod
    def marshal(cls, model: DocumentTypeModel) -> "DocumentType":
        return cls(id=strawberry.ID(str(model.id)), description=model.description, afip_code=model.afip_code)
