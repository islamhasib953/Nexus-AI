# Phase 12 local load benchmark

The reproducible command is:

```powershell
cd apps/api
uv run python scripts/phase12_load_test.py
```

It sends 100 authenticated health requests with eight concurrent workers against the in-process FastAPI test client and reports p50, p95, and maximum latency. This is a local smoke baseline, not a production capacity claim. PostgreSQL, Redis, Qdrant, multiple API workers, and a real network are required for a release-grade capacity test.
