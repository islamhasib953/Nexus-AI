import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.persistence.models import Document, DocumentChunk
from app.rag.chunking import chunk_text, sanitize_for_retrieval
from app.rag.embeddings import EmbeddingModel, HashEmbeddingModel
from app.rag.models import Citation, RetrievalResult, metadata
from app.rag.vector_store import QdrantVectorStore, VectorPoint


class DocumentService:
    def __init__(
        self,
        qdrant: QdrantVectorStore | None = None,
        embedder: EmbeddingModel | None = None,
    ) -> None:
        self.embedder = embedder or HashEmbeddingModel()
        self.qdrant = qdrant or QdrantVectorStore()

    def ingest(
        self,
        db: Session,
        *,
        organization_id: str,
        owner_id: str,
        workspace: str,
        title: str,
        content: str,
        source_uri: str | None = None,
        source_type: str = "upload",
        metadata_value: dict[str, object] | None = None,
    ) -> Document:
        clean_content, flagged = sanitize_for_retrieval(content)
        content_hash = hashlib.sha256(clean_content.encode("utf-8")).hexdigest()
        current = db.scalar(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.title == title,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.version.desc())
        )
        version = (current.version + 1) if current else 1
        if current is not None:
            current.status = "superseded"
        document = Document(
            organization_id=organization_id,
            owner_id=owner_id,
            workspace=workspace,
            title=title,
            source_uri=source_uri,
            source_type=source_type,
            version=version,
            content_hash=content_hash,
            status="ready",
            metadata_json=metadata({**(metadata_value or {}), "prompt_injection_flagged": flagged}),
        )
        db.add(document)
        db.flush()
        chunks = chunk_text(clean_content)
        points: list[VectorPoint] = []
        for index, text in enumerate(chunks):
            embedding = self.embedder.embed(text)
            chunk = DocumentChunk(
                document_id=document.id,
                organization_id=organization_id,
                workspace=workspace,
                chunk_index=index,
                content=text,
                embedding_json=json.dumps(embedding),
                metadata_json=metadata({"injection_flagged": flagged}),
            )
            db.add(chunk)
            db.flush()
            points.append(
                VectorPoint(
                    chunk.id,
                    embedding,
                    {
                        "document_id": document.id,
                        "organization_id": organization_id,
                        "workspace": workspace,
                        "version": version,
                    },
                )
            )
        try:
            self.qdrant.upsert(points, self.embedder.dimensions)
        except Exception:
            document.status = "ready_local_index"
        return document

    def delete(self, db: Session, *, document_id: str, organization_id: str) -> bool:
        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None),
            )
        )
        if not document:
            return False
        document.deleted_at = datetime.now(UTC)
        document.status = "deleted"
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        try:
            self.qdrant.delete_document(document.id)
        except Exception:
            pass
        return True

    def search(
        self,
        db: Session,
        *,
        organization_id: str,
        user_id: str,
        workspace: str,
        query: str,
        limit: int = 5,
        min_score: float = 0.12,
    ) -> RetrievalResult:
        query_vector = self.embedder.embed(query)
        rows = db.scalars(
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.workspace == workspace,
                Document.organization_id == organization_id,
                Document.workspace == workspace,
                Document.deleted_at.is_(None),
                Document.status.in_(["ready", "ready_local_index"]),
            )
            .order_by(DocumentChunk.created_at.desc())
        ).all()
        scored: list[tuple[float, DocumentChunk, Document]] = []
        for chunk in rows:
            document = db.get(Document, chunk.document_id)
            if (
                document is None
                or document.organization_id != organization_id
                or document.workspace != workspace
            ):
                continue
            score = self.embedder.similarity(query_vector, json.loads(chunk.embedding_json))
            if score >= min_score:
                scored.append((score, chunk, document))
        scored.sort(key=lambda item: item[0], reverse=True)
        evidence = tuple(
            Citation(
                document_id=document.id,
                title=document.title,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                score=score,
                excerpt=chunk.content[:500],
            )
            for score, chunk, document in scored[:limit]
        )
        return RetrievalResult(
            query=query,
            evidence=evidence,
            supported=bool(evidence),
            reason=None if evidence else "insufficient_authorized_evidence",
        )
