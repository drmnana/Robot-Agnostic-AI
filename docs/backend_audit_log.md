# Backend Audit Log

## Purpose

The backend audit log records protected API authorization decisions.

It is separate from mission report audit data:

- Mission report audit records what happened during a mission.
- Backend audit records who attempted protected API calls and whether the backend allowed or denied them.

## Storage

Backend audit events are stored in the same SQLite database as mission reports:

```text
/workspace/data/orimus.db
```

The table is separate:

```text
backend_audit_events
```

This is simpler for the pilot. A future migration can move backend audit events to a dedicated datastore.

## Logged Events

Every protected mission command API call is logged:

- allowed requests
- denied requests

Fields include:

- `created_at_sec`
- `event_type`
- `operator_id`
- `decision`
- `mission_id`
- `command_type`
- `reason`
- `request_path`
- `source_ip`
- `retention_class`

`retention_class` defaults to `standard` for future retention policy work.

## Source IP

Source IP logging is controlled by:

```text
ORIMUS_LOG_SOURCE_IP
```

Default:

```text
true
```

When disabled, `source_ip` is stored as `null`.

## Append-Only Constraint

At the application layer, backend audit writes are append-only.

The public write method is:

```text
record_event
```

The backend does not expose update or delete methods for audit events.

## API

```text
GET /audit/events
```

Filters:

- `operator_id`
- `decision`
- `event_type`
- `date_from`
- `date_to`

## Dashboard

The operator dashboard includes an API Audit panel that reads from `GET /audit/events`.

The panel supports operator, decision, event type, and date filters. Denied attempts use a stronger warning treatment than allowed attempts so they can be spotted while scrolling.

## Deferred Export And Verification

API Audit export and verifier support are deferred.

Mission History already supports filter, drilldown, JSON export, and verifier workflows. API Audit will eventually need similar review parity, but the current scope is dashboard browsing and filtering.

## Scope

This log records backend API authorization decisions. It does not replace mission reports, evidence packages, ROS safety events, or hardware safety logs.
