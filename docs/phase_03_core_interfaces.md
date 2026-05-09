# Phase 03 - Core Interfaces

## Goal

Define the common language used between the system components.

This includes commands, robot state, payload state, mission state, perception events, safety events, and logs.

## Why This Comes Before Heavy Implementation

Interfaces keep the project modular.

If every component agrees on the same message formats, we can replace one robot, sensor, AI model, or dashboard without rewriting the whole system.

## Main Tasks

- Define robot command interface.
- Define robot telemetry interface.
- Define mission command interface.
- Define payload command interface.
- Define perception event interface.
- Define safety event interface.
- Define system health interface.
- Decide which interfaces are ROS 2 messages, backend API schemas, or both.

## Example Interfaces

Robot command:

```json
{
  "command": "walk_velocity",
  "linear_x": 0.3,
  "linear_y": 0.0,
  "yaw_rate": 0.1
}
```

Perception event:

```json
{
  "event_type": "person_detected",
  "confidence": 0.92,
  "source": "front_camera",
  "timestamp": "2026-05-08T12:00:00Z"
}
```

## Outputs

- Interface specification document
- Initial ROS 2 message/action/service definitions
- Backend API schema draft
- Naming conventions

## Completion Criteria

This phase is complete when the major components can communicate through documented, versioned interfaces.

