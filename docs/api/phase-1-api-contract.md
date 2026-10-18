# Phase 1 initial API and event contract

The public API is versioned under `/api/v1`, uses JSON for ordinary request/response bodies, and uses SSE for server-to-client run events. Authentication uses a bearer/session mechanism behind the identity adapter. Every endpoint derives the request context server-side.

The machine-readable design source is [openapi-v1.yaml](openapi-v1.yaml). It is a draft contract until FastAPI generates the implementation OpenAPI document.

## Endpoint groups

| Method and path | Purpose | Authorization |
| --- | --- | --- |
| `GET /api/v1/me` | Current resolved identity, memberships, and permitted workspace summary | Authenticated user |
| `GET /api/v1/conversations` | Paginated authorized conversations | Workspace/member policy |
| `POST /api/v1/conversations` | Create a scoped conversation | Workspace/member policy |
| `GET /api/v1/conversations/{conversationId}` | Read conversation and authorized messages | Resource policy |
| `POST /api/v1/conversations/{conversationId}/runs` | Submit a user message and create a run | Resource/capability policy |
| `GET /api/v1/runs/{runId}` | Read authorized run status and summary | Resource policy |
| `POST /api/v1/runs/{runId}/cancel` | Request cooperative cancellation | Requester/administrator policy |
| `GET /api/v1/runs/{runId}/events` | SSE status and message events | Resource policy rechecked on connect |
| `POST /api/v1/documents` | Create authorized document ingestion request | Administrator/source policy |
| `GET /api/v1/documents/{documentId}` | Read document lifecycle metadata | Source/resource policy |
| `GET /api/v1/admin/audit-events` | Paginated tenant audit view | Tenant administrator policy |
| `POST /api/v1/approvals/{approvalId}/decision` | Future approve/reject action | Exact approver/action policy; no R1 live mutation |

## Common conventions

- IDs are UUIDs. List endpoints use stable cursor pagination: `limit` and `cursor`.
- A successful asynchronous submission returns `202 Accepted` with the new run/job state and links to its event stream.
- Request body schemas are Pydantic-defined and published through FastAPI OpenAPI. Unknown fields are rejected on security-sensitive requests.
- The server returns a request/correlation ID in response headers and bodies where applicable.
- APIs never return provider credentials, raw secret values, private reasoning, unauthorized document content, or an approval token usable for another action.

## Error envelope

```json
{
  "error": {
    "code": "authorization_denied",
    "message": "You do not have access to this resource.",
    "request_id": "uuid",
    "retryable": false,
    "details": []
  }
}
```

Codes include `validation_failed`, `unauthenticated`, `authorization_denied`, `not_found`, `conflict`, `rate_limited`, `run_cancelled`, `approval_required`, `provider_unavailable`, `dependency_unavailable`, and `internal_error`. A `not_found` response may be returned instead of `authorization_denied` where revealing resource existence is unsafe.

## SSE event envelope

Each event has an SSE `id`, event type, and JSON data with `run_id`, monotonic `sequence`, UTC `occurred_at`, and a sanitized payload. Stable initial event types: `run_started`, `status_changed`, `message_delta`, `agent_started`, `agent_completed`, `retrieval_completed`, `tool_started`, `tool_completed`, `approval_required`, `usage_updated`, `run_completed`, `run_failed`, and `run_cancelled`.

The client reconnects with `Last-Event-ID`; the server reauthorizes the run and replays persisted events after that sequence when allowed. `message_delta` contains displayable generated text only, never internal chain-of-thought.
