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

## Completion Criteria

This phase is complete when software clients can create missions, monitor state, and receive events through the backend.

