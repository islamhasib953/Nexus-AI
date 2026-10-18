"""Small reproducible local smoke benchmark; not a substitute for distributed load testing."""

import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def main() -> None:
    client = TestClient(create_app(Settings(database_url="sqlite:///./phase12-load.db")))
    token = client.post("/api/v1/auth/dev/session", json={"profile": "internal"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}

    def request() -> float:
        started = time.perf_counter()
        response = client.get("/api/v1/health/live", headers=headers)
        response.raise_for_status()
        return (time.perf_counter() - started) * 1000

    with ThreadPoolExecutor(max_workers=8) as pool:
        samples = list(pool.map(lambda _: request(), range(100)))
    print(
        {
            "requests": len(samples),
            "p50_ms": round(statistics.median(samples), 2),
            "p95_ms": round(sorted(samples)[94], 2),
            "max_ms": round(max(samples), 2),
        }
    )


if __name__ == "__main__":
    main()
