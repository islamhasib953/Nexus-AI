import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.persistence.models import ResponseCache


class ExactResponseCache:
    def make_key(
        self,
        *,
        organization_id: str,
        owner_id: str,
        workspace: str,
        model_id: str,
        route_kind: str,
        prompt: str,
        context_fingerprint: str = "none",
    ) -> str:
        raw = "|".join(
            [
                organization_id,
                owner_id,
                workspace,
                model_id,
                route_kind,
                context_fingerprint,
                prompt,
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, db: Session, cache_key: str) -> ResponseCache | None:
        entry = db.scalar(select(ResponseCache).where(ResponseCache.cache_key == cache_key))
        if entry is None:
            return None
        expires_at = entry.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            db.delete(entry)
            db.flush()
            return None
        return entry

    def put(
        self,
        db: Session,
        *,
        organization_id: str,
        owner_id: str,
        workspace: str,
        cache_key: str,
        content: str,
        model_id: str,
        route_kind: str,
        ttl_seconds: int,
        source_revision: str = "static",
    ) -> ResponseCache:
        entry = db.scalar(select(ResponseCache).where(ResponseCache.cache_key == cache_key))
        if entry is None:
            entry = ResponseCache(
                organization_id=organization_id,
                owner_id=owner_id,
                workspace=workspace,
                cache_key=cache_key,
                content=content,
                model_id=model_id,
                route_kind=route_kind,
                source_revision=source_revision,
                expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
            )
            db.add(entry)
        else:
            entry.content = content
            entry.expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        db.flush()
        return entry

    def invalidate_source(self, db: Session, source_revision: str) -> int:
        result = db.execute(
            delete(ResponseCache).where(ResponseCache.source_revision == source_revision)
        )
        return result.rowcount or 0

    def invalidate_tenant(self, db: Session, organization_id: str) -> int:
        result = db.execute(
            delete(ResponseCache).where(ResponseCache.organization_id == organization_id)
        )
        return result.rowcount or 0
