import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    document_id: str
    title: str
    chunk_id: str
    chunk_index: int
    score: float
    excerpt: str

    def as_dict(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "score": round(self.score, 4),
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    evidence: tuple[Citation, ...]
    supported: bool
    reason: str | None = None

    def prompt_context(self) -> str:
        if not self.evidence:
            return "No authorized evidence was found. Do not invent company-specific facts."
        return "\n\n".join(
            f"[{index}] {item.title}: {item.excerpt}" for index, item in enumerate(self.evidence, 1)
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "supported": self.supported,
            "reason": self.reason,
            "citations": [item.as_dict() for item in self.evidence],
        }


def metadata(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
