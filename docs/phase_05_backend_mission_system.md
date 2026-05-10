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
- `GET /reports/latest`

The backend does not yet publish ROS 2 mission commands. That is the next backend integration step.

## Completion Criteria

This phase is complete when software clients can create missions, monitor state, and receive events through the backend.
