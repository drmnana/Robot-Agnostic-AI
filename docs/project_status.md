# Project Status

Project name: ORIMUS

## Current Phase

Simulation-first vertical slice and audit foundation are complete.

The project is now ready for repeatability, scenario coverage, dashboard refinement, and non-hardware autonomy scaffolding.

Real robot platform integration and real payload integration are deferred for CTO review.

## Prominent Deferred Work

See [CTO Review Items](cto_review_items.md).

Do not finalize these without CTO guidance:

- real robot platform adapter
- real robot command/telemetry mapping
- hardware emergency stop and manual override model
- real payload adapter
- real payload artifact formats
- real payload metadata taxonomy
- real perception model selection

## Completed Foundation

- Project architecture reference.
- Project phase roadmap.
- Decision log.
- Glossary.
- Windows-friendly Docker development setup.
- Git, WSL2, Docker Desktop setup.
- ROS 2 Humble development container.
- `.gitattributes` for Windows/Linux line-ending stability.
- Safety assumptions document.

## Completed ROS 2 Simulation Stack

- `core_interfaces` shared message definitions.
- `mock_go2x_driver` simulation-first robot driver.
- `safety_manager` command safety gate.
- `mission_manager` YAML-driven mission sequencer.
- `payload_manager` generic payload gate.
- `mock_payloads` mock inspection camera.
- `report_manager` mission report collector.
- `orimus_bringup` launch package.
- ROS-aware `mission_api_bridge`.

## Completed Mission Features

- YAML mission configuration.
- Mission YAML schema file and validator.
- Mission steps targeting robot or payload.
- Demo mission with mock inspection scan.
- Simulated mission scenario library.
- Scenario test harness with single-scenario and run-all modes.
- Mission command flow: start, pause, resume, cancel, reset.
- Mission events.
- Rolling runtime event history.
- Sector metadata for audit filtering.

## Completed Backend And Dashboard

- FastAPI backend.
- Dashboard served from `/dashboard/`.
- Mission list and mission command UI.
- Live runtime state.
- Operator ID field.
- Operator-to-API command policy.
- Backend API audit log.
- API Audit dashboard panel.
- API Audit Package Schema v1.0.
- API Audit export and verifier.
- Human-readable PDF report export.
- Mission History panel.
- Report filters.
- Report timeline.
- Evidence drilldowns.
- Mission replay viewer.
- Backend liveness and readiness endpoints.
- Persistent dashboard readiness indicator.
- Normalized event severity contract and dashboard labels.
- Backend API contract documentation.
- Committed OpenAPI artifact with drift test.
- CI-ready local verification command.
- URL-addressable dashboard operator tabs.

## Completed Audit, Evidence, And Replay

- SQLite mission audit database at `data/orimus.db`.
- Persistent report list/detail endpoints.
- SHA-256 mission report content hashes.
- JSON Evidence Package Schema v1.0.
- Evidence package verifier.
- Generic evidence artifact registry.
- Hash-checked artifact downloads.
- Deterministic ZIP Evidence Bundle Schema v1.0.
- Evidence bundle verifier.
- Dashboard artifact links.
- Dashboard export buttons for JSON and bundle.
- Replay endpoint and dashboard replay controls.
- URL-addressable replay frame state.

## Current Integration Seams

Robot seam:

- Today: `mock_go2x_driver`.
- Future: real platform adapter after CTO review.

Payload seam:

- Today: `mock_inspection_camera`.
- Future: real payload adapter after CTO review.

See [Current Architecture Snapshot](current_architecture_snapshot.md) for details.

## Work We Can Do Before CTO Review

1. Add WebSocket or SSE live event streaming.
2. Add report/PDF layout branding polish.

## Recommended Next Step

Create a **Live Event Streaming** ticket.

This will reduce dashboard polling and prepare the operator UI for real-time mission monitoring without changing robot or payload contracts.
