#!/usr/bin/env bash
set -euo pipefail
: "${PREVIOUS_API_IMAGE:?set PREVIOUS_API_IMAGE}"
: "${PREVIOUS_WEB_IMAGE:?set PREVIOUS_WEB_IMAGE}"
export NEXUS_API_IMAGE="$PREVIOUS_API_IMAGE"
export NEXUS_WEB_IMAGE="$PREVIOUS_WEB_IMAGE"
docker compose -f docker-compose.production.yml --env-file .env.production up -d
curl --fail --retry 10 http://127.0.0.1:8000/api/v1/health/ready
