# Live Event Streaming

ORIMUS exposes a read-only Server-Sent Events stream for dashboard runtime updates:

```text
GET /runtime/stream
```

SSE is intentionally one-way. Mission commands still use protected POST endpoints, so the streaming channel does not become a second command path.

## Event Types

- `runtime_state`: current runtime state, equivalent to `GET /runtime/state`
- `readiness`: backend readiness payload, equivalent to `GET /readiness`
- `heartbeat`: stream liveness heartbeat
- `runtime_error`: runtime bridge/read error payload

## Intervals

- Runtime state interval: 2 seconds
- Heartbeat interval: 20 seconds

The dashboard watches for missed heartbeats and switches to polling fallback after 45 seconds. That keeps failover inside the 30-60 second operator window.

When SSE reconnects, dashboard runtime/readiness polling stops and streaming resumes.

## Browser Connection Limit

Major browsers commonly limit each origin to about 6 concurrent HTTP connections. SSE counts as one connection.

Multiple ORIMUS dashboard tabs can share that browser budget. If multi-tab usage becomes a real operational issue, a future ticket can add a `SharedWorker` connection coordinator so tabs share one SSE connection.

## Fallback

The dashboard uses `EventSource` when available.

If EventSource is unavailable, errors, or heartbeats stop:

- runtime polling resumes every 2 seconds
- readiness polling resumes every 20 seconds
- SSE retry is attempted every 15 seconds
- polling stops when SSE reconnects
