# Phase 10 - Operator Dashboard

## Goal

Build the human control interface for viewing robot state, missions, maps, video, payloads, and alerts.

## Why This Comes After Backend Basics

The dashboard should reflect real system behavior instead of being only a static mockup.

However, a simple prototype can be created earlier if needed for planning.

## Main Tasks

- Create dashboard application.
- Show robot connection state.
- Show battery and health.
- Show mission state.
- Show live events and alerts.
- Show video or sensor feeds.
- Add mission start, pause, resume, cancel, reset.
- Add manual override controls.
- Add emergency stop control.

## Dashboard Views

- Overview
- Mission planner
- Live robot status
- Video and sensor feeds
- Map
- Event log
- Payload controls
- Settings

## Outputs

- Operator dashboard
- Mission control UI
- Live robot status panel
- Payload status panel
- Event log viewer

## Initial Dashboard Prototype

The first dashboard prototype is located in `dashboard/` and is served by the backend at:

```text
http://localhost:8000/dashboard/
```

Current capabilities:

- Lists mission YAML configs through `GET /missions`.
- Selects one mission for operator commands.
- Captures a development-mode operator ID for command attribution.
- Sends start, pause, resume, cancel, and reset through backend mission endpoints.
- Shows backend policy denials when an operator is not allowed to call a mission command API.
- Polls `GET /runtime/state` for mission, robot, payload, perception, and safety status.
- Shows a rolling event history from ROS mission, perception, and safety events.
- Shows mission report history, selected report summary, content hash, and report timeline.
- Filters mission history by outcome, mission, sector, date range, perception event type, safety-event presence, and blocked command evidence.
- Shows selected report detail as a unified chronological audit timeline with command verdicts, safety links, perception evidence metadata, payload results, and report hash copy support.
- Shows artifact links in perception drilldowns when evidence files are present, and cleanly reports that no artifact was captured when absent.
- Exports the selected mission report as a JSON-only ORIMUS Evidence Package.
- Shows backend API audit events with filters for operator, decision, event type, and date range.
- Gives denied API attempts a distinct warning treatment so authorization failures stand out during review.
- Shows backend and ROS bridge connection status.

This is intentionally a compact operational screen, not a final polished control station.

## Completion Criteria

This phase is complete when an operator can monitor the system and control basic missions from the dashboard.
