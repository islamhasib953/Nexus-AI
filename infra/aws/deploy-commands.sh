#!/usr/bin/env bash
set -euo pipefail
cd /opt/nexus-ai
export NEXUS_API_IMAGE="${NEXUS_API_IMAGE:?missing API image}"
export NEXUS_WEB_IMAGE="${NEXUS_WEB_IMAGE:?missing web image}"
docker compose -f docker-compose.production.yml --env-file .env.production pull
docker compose -f docker-compose.production.yml --env-file .env.production run --rm api uv run alembic upgrade head
docker compose -f docker-compose.production.yml --env-file .env.production up -d --remove-orphans
curl --fail --retry 10 http://127.0.0.1:8000/api/v1/health/ready
