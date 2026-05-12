# Backend Health And Readiness

ORIMUS exposes two distinct backend health contracts.

## Liveness

`GET /healthz`

Liveness returns `200` when the backend process can answer HTTP requests. It does not check dependencies, files, SQLite, ROS 2, or mission configuration.

Use this for deployment process liveness checks.

## Readiness

`GET /readiness`

Readiness reports whether the backend is ready for operator use and demo pre-flight checks.

The response includes:

- overall `status`: `ready`, `degraded`, or `not_ready`
- `cached`: whether expensive checks came from the short readiness cache
- `cache_ttl_sec`
- `generated_at`
- per-check status records

Required check failures make the service `not_ready`.
Optional degraded checks make the service `degraded`.

Current readiness checks include:

- backend process responsiveness
- mission config directory presence
- report database parent presence
- latest report parent presence
- mission YAML validation
- SQLite reachability
- artifact root writability
- latest report directory writability
- operator policy parsing
- ROS mission API bridge health

The ROS bridge check is optional because the backend dashboard can still render historical audit data when ROS is offline.

## Cache Behavior

Expensive readiness checks are cached for 10 seconds so multiple dashboard operators do not repeatedly run YAML validation and filesystem probes.

Use:

```text
GET /readiness?fresh=true
```

to bypass the cache and force a fresh dependency check.

The dashboard polls readiness automatically every 20 seconds and keeps a persistent header indicator visible.
