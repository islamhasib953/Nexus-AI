from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_principal
from app.persistence.models import Document
from app.rag.service import DocumentService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class IngestDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=2_000_000)
    source_uri: str | None = Field(default=None, max_length=500)
    source_type: str = Field(default="upload", max_length=40)
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_db(request: Request):
    yield from request.app.state.database.sessions()


def get_service(request: Request) -> DocumentService:
    return request.app.state.documents


@router.post("/documents", status_code=201)
def ingest_document(
    body: IngestDocumentRequest,
    principal: Principal = Depends(require_principal),
    service: DocumentService = Depends(get_service),
    db: Session = Depends(get_db),
):
    document = service.ingest(
        db,
        organization_id=principal.organization_id,
        owner_id=principal.user_id,
        workspace=principal.workspace,
        title=body.title,
        content=body.content,
        source_uri=body.source_uri,
        source_type=body.source_type,
        metadata_value=body.metadata,
    )
    db.commit()
    return {
        "id": document.id,
        "title": document.title,
        "version": document.version,
        "status": document.status,
        "content_hash": document.content_hash,
    }


@router.get("/documents")
def list_documents(
    principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
):
    documents = db.scalars(
        select(Document)
        .where(
            Document.organization_id == principal.organization_id,
            Document.workspace == principal.workspace,
            Document.deleted_at.is_(None),
            Document.status == "ready",
        )
        .order_by(Document.updated_at.desc())
    ).all()
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "version": item.version,
                "status": item.status,
                "source_type": item.source_type,
            }
            for item in documents
        ]
    }


@router.post("/search")
def search_knowledge(
    body: dict[str, Any],
    principal: Principal = Depends(require_principal),
    service: DocumentService = Depends(get_service),
    db: Session = Depends(get_db),
):
    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=422, detail="query is required")
    result = service.search(
        db,
        organization_id=principal.organization_id,
        user_id=principal.user_id,
        workspace=principal.workspace,
        query=query,
        limit=int(body.get("limit", 5)),
    )
    return result.as_dict()


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    principal: Principal = Depends(require_principal),
    service: DocumentService = Depends(get_service),
    db: Session = Depends(get_db),
):
    if not service.delete(db, document_id=document_id, organization_id=principal.organization_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    db.commit()
