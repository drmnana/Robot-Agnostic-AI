# Phase 05 - Backend Mission System

## Goal

Build the backend service that manages missions, robot state, payload state, logs, and operator commands.

## Why Backend Before Full Frontend

The dashboard needs something real to connect to.

The backend becomes the control center between the operator interface, ROS 2, AI planner, mission state, and logs.

## Main Tasks

- Create backend API service.
- Define mission objects.
- Define robot status endpoints.
- Define payload status endpoints.
- Add mission start, pause, resume, cancel.
- Add event logging.
- Add user command validation.
- Add WebSocket or streaming API for live updates.

## Recommended Backend Responsibilities

- Store mission definitions.
- Track active mission state.
- Receive robot telemetry.
- Receive perception events.
- Send approved commands to ROS 2 layer.
- Notify dashboard of updates.
- Record logs.

## Outputs

- Backend service
- Mission API
- Robot state API
- Payload state API
- Event logging system
- Live update stream

## Initial ROS 2 Mission Skeleton

The first mission manager exists as a ROS 2 package named `mission_manager`.

It currently runs a simple demo mission:

```text
stand -> walk_forward -> stop -> sit
```

The mission steps are now loaded from YAML config files in `configs/missions/`.

The first config is:

```text
configs/missions/demo_forward_stop.yaml
```

This is not the final backend mission system. It is the first vertical slice proving that mission logic can load a mission definition and send requested commands through the safety manager to the mock robot.

Mission steps can now target:

- `robot`: publishes to `/robot/command_request`.
- `payload`: publishes to `/payload/command_request`.

The demo mission now includes a mock inspection scan step.

Mission execution now also emits structured mission events on `/mission/events`.

The `report_manager` package collects mission states, mission events, robot state, payload state, payload results, perception events, and safety events into a JSON mission report.

The mission manager now accepts operator-style mission commands on `/mission/command`:

- `start`
- `pause`
- `resume`
- `cancel`
- `reset`

## Initial Backend Skeleton

The first backend service exists in `backend/`.

Current endpoints:

- `GET /health`
- `GET /missions`
- `GET /missions/{mission_id}`
- `POST /missions/{mission_id}/start`
- `POST /missions/{mission_id}/pause`
- `POST /missions/{mission_id}/resume`
- `POST /missions/{mission_id}/cancel`
- `POST /missions/{mission_id}/reset`
- `GET /audit/events`
- `GET /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/download`
- `GET /runtime/state`
- `GET /runtime/mission`
- `GET /runtime/robot`
- `GET /runtime/payload`
- `GET /runtime/perception`
- `GET /runtime/safety`
- `GET /runtime/events`
- `GET /reports`
- `GET /reports/{report_id}/export-bundle`
- `GET /reports/{report_id}/export`
- `GET /reports/latest`
- `GET /reports/{report_id}`

The backend forwards mission command requests to the ROS-aware mission API bridge.
The backend forwards live runtime state requests from the ROS-aware mission API bridge.
The backend reads persisted mission report history from the SQLite audit database.
The bridge URL is configured through `ORIMUS_MISSION_API_BRIDGE_URL`.

Mission command requests accept `X-ORIMUS-Operator` for development-mode attribution. Missing or blank operator values are recorded explicitly as `anonymous`.

This is not production authentication. The value is self-asserted and trust-based; production deployment will require real authentication such as JWT, mTLS, or SSO.

Mission command requests are now checked against `configs/operator_policy.yaml` before forwarding to ROS.

This is operator-to-API authorization. It does not replace, augment, or coordinate with the robot's `safety_manager` or any hardware-level safety constraints. Those are independent layers.

Allowed and denied protected API calls are recorded in `backend_audit_events` inside the same SQLite database as mission reports. Backend audit events are append-only at the application layer.

Mission evidence artifacts are indexed in `evidence_artifacts` inside the same SQLite database. Artifact downloads verify the stored SHA-256 hash before returning file content.

Mission YAML metadata now includes `sector`, allowing finalized reports to be searched by operating area.

`GET /reports` supports query filters for:

- `outcome`
- `mission_id`
- `sector`
- `date_from`
- `date_to`
- `perception_event_type`
- `has_safety_event`
- `command_blocked`

`GET /reports/{report_id}/export` returns an ORIMUS Evidence Package JSON document using schema version `1.0`.
`GET /reports/{report_id}/export-bundle` returns a deterministic ZIP evidence bundle containing the evidence package, manifest, and artifact files.

## ROS-Aware Mission API Bridge

The `mission_api_bridge` ROS 2 package exposes HTTP endpoints from inside the ROS runtime and publishes mission commands to `/mission/command`.

Bridge endpoints:

- `GET /health`
- `POST /missions/{mission_id}/start`
- `POST /missions/{mission_id}/pause`
- `POST /missions/{mission_id}/resume`
- `POST /missions/{mission_id}/cancel`
- `POST /missions/{mission_id}/reset`
- `GET /runtime/state`
- `GET /runtime/mission`
- `GET /runtime/robot`
- `GET /runtime/payload`
- `GET /runtime/perception`
- `GET /runtime/safety`
- `GET /runtime/events`

This gives ORIMUS a working HTTP-to-ROS command path and a ROS-to-HTTP live state path.

## Completion Criteria

This phase is complete when software clients can create missions, monitor state, and receive events through the backend.
