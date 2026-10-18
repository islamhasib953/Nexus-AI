# Phase 1 deployment plan and scaling roadmap

## Initial topology

Development uses Docker Compose with a web workspace, FastAPI API, worker, PostgreSQL, Qdrant, and optionally Redis. The first production candidate is one AWS EC2 host running versioned containers behind TLS ingress, with managed PostgreSQL/Qdrant/Redis evaluated against budget and operational requirements. It is explicitly a single point of failure and not an availability promise.

Secrets are environment references in development and AWS Secrets Manager or Parameter Store references in AWS. IAM roles supply access; secrets never ship in images, source control, client bundles, or logs. GitHub Actions validates, builds, scans, and publishes immutable images before an approved deploy.

## Scale triggers and response

| Observed trigger | First response | Later response |
| --- | --- | --- |
| API CPU, connection, or SSE saturation | Add stateless API replicas and compatible ingress | Separate streaming gateway only with evidence |
| Ingestion queue delay or job backlog | Add worker replicas; throttle ingestion | Adopt managed queue after delivery/throughput analysis |
| PostgreSQL load | Query/index tuning, pool controls, managed database evaluation | Read replicas/partitioning only after measured need |
| Qdrant latency/index growth | Tune collections and capacity | Dedicated/managed vector cluster |
| Provider rate limits/unavailability | Route to configured eligible free/local fallback and queue deferrable work | Add evaluated providers only under policy/budget |
| Tool-specific load/failure | Circuit-break the adapter and isolate credentials | Extract tool service when independent operation is justified |

## Operations baseline

OpenTelemetry-compatible traces correlate HTTP request, run, agent, retrieval, provider, job, and tool spans. Metrics cover request/run latency, SSE reconnects, tokens/cost, cache route/result, provider failures, retrieval/citation result, job lease/retry/dead-letter state, authorization denials, and data-store health. Alert thresholds are defined from measured baselines in later phases, not invented here.
