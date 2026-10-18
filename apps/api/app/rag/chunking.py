import re

INJECTION_MARKERS = re.compile(
    r"ignore\s+(all|any|previous)|system\s+message|developer\s+instruction|reveal\s+secrets",
    re.I,
)


def sanitize_for_retrieval(text: str) -> tuple[str, bool]:
    """Keep evidence as data and flag instruction-like content for safe prompting."""
    flagged = bool(INJECTION_MARKERS.search(text))
    return text, flagged


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
