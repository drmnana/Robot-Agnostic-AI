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
- `GET /runtime/state`
- `GET /runtime/mission`
- `GET /runtime/robot`
- `GET /runtime/payload`
- `GET /runtime/perception`
- `GET /runtime/safety`
- `GET /reports/latest`

The backend forwards mission command requests to the ROS-aware mission API bridge.
The backend forwards live runtime state requests from the ROS-aware mission API bridge.
The bridge URL is configured through `ORIMUS_MISSION_API_BRIDGE_URL`.

## ROS-Aware Mission API Bridge

The `mission_api_bridge` ROS 2 package exposes HTTP endpoints from inside the ROS runtime and publishes mission commands to `/mission/command`.

Bridge endpoints:

- `GET /health`
- `POST /missions/{mission_id}/start`
- `POST /missions/{mission_id}/pause`
- `POST /missions/{mission_id}/resume`
- `POST /missions/{mission_id}/cancel`
- `GET /runtime/state`
- `GET /runtime/mission`
- `GET /runtime/robot`
- `GET /runtime/payload`
- `GET /runtime/perception`
- `GET /runtime/safety`

This gives ORIMUS a working HTTP-to-ROS command path and a ROS-to-HTTP live state path.

## Completion Criteria

This phase is complete when software clients can create missions, monitor state, and receive events through the backend.
