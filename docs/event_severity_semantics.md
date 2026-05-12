# Event Severity Semantics

ORIMUS uses one canonical severity vocabulary for operator-facing events:

- `info`
- `notice`
- `warning`
- `critical`

The source of truth is `backend/app/event_severity.py`.
The JSON Schema reference is `configs/event_severity_schema.json`.

Severity is part of the API contract. Dashboard styling must not invent new severity levels.

## Meaning

`info`: normal background information.

`notice`: normal but operationally relevant state change or successful safety check.

`warning`: condition that deserves operator attention but does not prove immediate failure.

`critical`: blocked action, failed required readiness check, denied protected API action, or other urgent condition.

## Mapping Rules

### Readiness

- `ready` -> `info`
- `degraded` -> `warning`
- `not_ready` with `requirement: required` -> `critical`
- `not_ready` with `requirement: optional` -> `warning`

### API Audit

- `allowed` -> `info`
- `denied` -> `critical`

### Safety Events

- `command_blocked: true` -> `critical`
- raw safety severity `critical`, `error`, or `fatal` -> `critical`
- raw safety severity `warning`, `warn`, or `degraded` -> `warning`
- other safety checks -> `notice`

### Mission Events

- event/message contains `failed`, `error`, or `emergency` -> `critical`
- event/message contains `canceled`, `paused`, or `blocked` -> `warning`
- event/message contains `started`, `running`, `completed`, or `step` -> `notice`
- otherwise -> `info`

### Perception Events

- event type contains `human`, `person`, `vehicle`, or `animal` -> `warning`
- otherwise -> `notice`

### Payload Results

- result/summary contains `failed`, `error`, or `hazard` -> `critical`
- result/summary contains `detected`, `warning`, or `anomaly` -> `warning`
- otherwise -> `notice`

### Robot Commands

- commands published to `robot/command` -> `notice`
- command requests or unknown command records -> `info`

## Dashboard Accessibility

The dashboard uses both visual color and text labels/icons:

- `[info] info`
- `[note] notice`
- `[warn] warning`
- `[!] critical`

Severity must remain visible without relying on color alone.
