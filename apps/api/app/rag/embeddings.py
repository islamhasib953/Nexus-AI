import hashlib
import math
from typing import Any, Protocol

import httpx


class EmbeddingModel(Protocol):
    model_id: str
    dimensions: int

    def embed(self, text: str) -> list[float]: ...

    @staticmethod
    def similarity(left: list[float], right: list[float]) -> float: ...


class HashEmbeddingModel:
    """Free deterministic development embedding, not a production quality claim."""

    model_id = "hash-embedding-v1"

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            values[index] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    @staticmethod
    def similarity(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))


class OpenAICompatibleEmbeddingModel:
    """Provider-neutral embedding adapter for local or hosted OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: str,
        model_id: str,
        dimensions: int,
        api_key: str = "",
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.dimensions = dimensions
        self.api_key = api_key
        self._client = client

    def embed(self, text: str) -> list[float]:
        if not self.base_url:
            raise RuntimeError("Embedding base URL is not configured.")
        endpoint = (
            self.base_url
            if self.base_url.endswith("/embeddings")
            else f"{self.base_url}/embeddings"
        )
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=15.0)
        try:
            response = client.post(
                endpoint,
                headers=headers,
                json={"model": self.model_id, "input": text},
            )
            response.raise_for_status()
            body: Any = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RuntimeError("Embedding provider request failed.") from error
        finally:
            if owns_client:
                client.close()
        try:
            vector = body["data"][0]["embedding"]
            values = [float(value) for value in vector]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError("Embedding provider returned an invalid vector.") from error
        if len(values) != self.dimensions or not all(math.isfinite(value) for value in values):
            raise RuntimeError("Embedding provider returned incompatible vector dimensions.")
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    @staticmethod
    def similarity(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))
