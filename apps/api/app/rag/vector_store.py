from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class VectorPoint:
    point_id: str
    vector: list[float]
    payload: dict[str, object]


class QdrantVectorStore:
    """Optional Qdrant adapter. Persistence remains safe when Qdrant is not configured."""

    def __init__(self, base_url: str = "", collection: str = "nexus_chunks") -> None:
        self.base_url = base_url.rstrip("/")
        self.collection = collection

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def upsert(self, points: list[VectorPoint], dimensions: int) -> None:
        if not self.enabled:
            return
        url = f"{self.base_url}/collections/{self.collection}/points"
        payload = {
            "points": [{"id": p.point_id, "vector": p.vector, "payload": p.payload} for p in points]
        }
        response = httpx.put(url, json=payload, timeout=5.0)
        response.raise_for_status()

    def delete_document(self, document_id: str) -> None:
        if not self.enabled:
            return
        url = f"{self.base_url}/collections/{self.collection}/points/delete"
        response = httpx.post(
            url,
            json={
                "points": [],
                "filter": {"must": [{"key": "document_id", "match": {"value": document_id}}]},
            },
            timeout=5.0,
        )
        response.raise_for_status()
