# ADR-0003: Use Server-Sent Events for initial run streaming

- Status: Accepted
- Date: 2026-10-18

## Decision

Use HTTP for commands and SSE for one-way run status and response deltas. Persist run events to support authorized reconnection/replay.

## Alternatives considered

- WebSockets: deferred because R1 needs server-to-client progress only; bidirectional transport adds connection/state complexity.
- Polling only: rejected because it degrades streamed response and run status experience.

## Consequences

The API must reauthorize SSE connections and support `Last-Event-ID`. WebSockets remain an option if a later feature proves a genuine bidirectional requirement.
