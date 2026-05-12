# ORIMUS

ORIMUS is a robot-agnostic autonomous AI mission system for quadruped robot platforms such as Unitree Go2, Unitree B2, Boston Dynamics Spot, Ghost Robotics platforms, and future ROS 2-compatible robots.

The project has a working simulation-first vertical slice with mission execution, audit history, artifact handling, evidence export, and replay review.

## Project Documents

- [Architecture Reference](docs/architecture_reference.md)
- [Current Architecture Snapshot](docs/current_architecture_snapshot.md)
- [CTO Review Items](docs/cto_review_items.md)
- [Project Phase Roadmap](docs/project_phase_roadmap.md)
- [Project Status](docs/project_status.md)
- [Decision Log](docs/decision_log.md)
- [Glossary](docs/glossary.md)
- [Docker Environment](docs/docker_environment.md)
- [Safety Assumptions](docs/safety_assumptions.md)
- [Evidence Package Schema v1.0](docs/evidence_package_schema_v1.md)
- [Evidence Package Verification](docs/evidence_package_verification.md)
- [Evidence Bundle Schema v1.0](docs/evidence_bundle_schema_v1.md)
- [Evidence Artifact Registry](docs/evidence_artifact_registry.md)
- [API Audit Package Schema v1.0](docs/api_audit_package_schema_v1.md)
- [Event Severity Semantics](docs/event_severity_semantics.md)
- [PDF Report Export](docs/pdf_report_export.md)
- [Mission Replay Viewer](docs/mission_replay_viewer.md)
- [Simulation Scenario Library](docs/simulation_scenario_library.md)
- [Scenario Test Harness](docs/scenario_test_harness.md)
- [Backend Health And Readiness](docs/backend_health_readiness.md)
- [Backend API Contract](docs/backend_api_contract.md)
- [Verification](docs/verification.md)
- [Dashboard Operator Workflow](docs/dashboard_operator_workflow.md)
- [Operator API Policy](docs/operator_api_policy.md)
- [Backend Audit Log](docs/backend_audit_log.md)

## Current Phase

Simulation-first vertical slice and audit foundation are complete.

Real robot platform integration and real payload integration are deferred for CTO review. See [CTO Review Items](docs/cto_review_items.md).

## Immediate Goals

- Add repeatable scenario test harnesses.
- Improve dashboard review workflows.
- Keep real robot and real payload decisions ready for CTO review.

## Current Direction

- First robot platform: Unitree Go2X
- First development target: simulation
- Preferred host operating system: Windows
- Preferred development strategy: Docker-based environment
- Real robot and real payload integration: deferred for CTO review

## Environment Status

- Git for Windows: installed
- WSL2: installed on the user's Windows account
- Docker Desktop: installed
- Docker validation: `hello-world` container ran successfully

## Development Container

The first development container uses ROS 2 Humble on Ubuntu 22.04 with Cyclone DDS selected for Unitree-oriented compatibility.

Start it with:

```powershell
docker compose run --rm ros2-dev
```

## ROS 2 Workspace

The first ROS 2 workspace is located in `ros2_ws/`.

Initial packages:

- `core_interfaces`: shared ROS 2 message definitions.
- `mock_go2x_driver`: simulation-first mock Unitree Go2X driver.
- `safety_manager`: safety gate for requested robot commands.
- `mission_manager`: first simple mission sequencer.
- `payload_manager`: safety-style gate for payload command requests.
- `mock_payloads`: first simulated payload adapters.
- `report_manager`: JSON mission report collector.
- `orimus_bringup`: launch files for starting ORIMUS runtime configurations.

## Mission Configs

Mission YAML files live in `configs/missions/`.
The mission YAML contract is defined in `configs/mission_schema.json`.

Current simulation scenarios include:

- `configs/missions/demo_forward_stop.yaml`
- `configs/missions/control_test.yaml`
- `configs/missions/perimeter_patrol.yaml`
- `configs/missions/artifact_inspection.yaml`
- `configs/missions/safety_speed_limit.yaml`
- `configs/missions/pause_resume_training.yaml`
- `configs/missions/policy_denial_demo.yaml`

Mission steps can target either `robot` or `payload`.
Mission YAML metadata includes a `sector` field so reports can be filtered by operating area.

Validate mission configs with:

```powershell
docker compose run --rm backend python backend/scripts/validate_missions.py
```

Run all scenario checks with:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh --all"
```

## Backend

The backend service is located in `backend/`.

Run the main verification command with:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

Current endpoints:

- `GET /health`
- `GET /healthz`
- `GET /readiness`
- `GET /missions`
- `GET /missions/{mission_id}`
- `POST /missions/{mission_id}/start`
- `POST /missions/{mission_id}/pause`
- `POST /missions/{mission_id}/resume`
- `POST /missions/{mission_id}/cancel`
- `POST /missions/{mission_id}/reset`
- `GET /audit/events`
- `GET /audit/events/export`
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
- `GET /reports/{report_id}/export-pdf`
- `GET /reports/{report_id}/replay`
- `GET /reports/latest`
- `GET /reports/{report_id}`

Mission command endpoints forward operator requests to the ROS-aware mission API bridge.
Development-mode operator identity is accepted through `X-ORIMUS-Operator`; missing or blank values are recorded as `anonymous`.
Mission command API calls are gated by `configs/operator_policy.yaml`. This is operator-to-API authorization only and does not replace the ROS `safety_manager`.
Allowed and denied protected API calls are recorded in the append-only backend audit table.
Runtime endpoints forward live state reads from the ROS-aware mission API bridge.
The bridge URL is configured with `ORIMUS_MISSION_API_BRIDGE_URL`.
Evidence artifact files are stored under `data/artifacts`, indexed in SQLite, and served through hash-checked artifact endpoints.
`GET /healthz` is a lightweight backend liveness endpoint.
`GET /readiness` validates mission YAML, SQLite, artifact/report writability, operator policy parsing, and ROS bridge availability. Expensive readiness checks are cached briefly and can be forced with `?fresh=true`.

`GET /reports` supports audit filters for `outcome`, `mission_id`, `sector`, `date_from`, `date_to`, `perception_event_type`, `has_safety_event`, and `command_blocked`.
`GET /reports/{report_id}/export` returns a JSON-only ORIMUS Evidence Package using schema version `1.0` with an export-level SHA-256 hash.
`GET /reports/{report_id}/export-bundle` returns a deterministic ZIP evidence bundle containing the evidence package JSON, manifest JSON, and referenced artifact files.
`GET /reports/{report_id}/replay` returns normalized chronological replay frames with filters for category, timestamp, operator, and command.

## Operator Dashboard

The first operator dashboard prototype is located in `dashboard/` and is served by the backend.

Open it at:

```text
http://localhost:8000/dashboard/
```

The dashboard can list missions, send mission commands, reset missions for repeated demos, display live runtime state, show mission event history, browse/filter persisted mission reports, and review backend API audit events.
The dashboard is organized into URL-addressable operator tabs for mission operations, mission history, API audit, and system readiness.
The dashboard includes an operator ID field for development-mode command attribution.

Mission reports are persisted to SQLite at `data/orimus.db` inside the workspace mount.
Each finalized report is stored with a SHA-256 content hash for audit traceability.
Report detail views show a unified chronological audit timeline, command safety verdicts, safety-event command links, perception evidence metadata, payload results, and report integrity fields.
Report detail views show artifact links when perception events reference stored evidence files, and degrade to "No artifact captured" when no artifact exists.
Selected reports can be exported as JSON evidence packages or ZIP evidence bundles.
Selected reports can also be exported as human-readable PDF summaries; JSON evidence packages remain the authoritative machine-readable records.
Evidence packages can be verified with `backend/scripts/verify_evidence_package.py`.
Evidence bundles can be verified with `backend/scripts/verify_evidence_bundle.py`.
The API Audit panel filters backend authorization events by operator, decision, event type, and date range, with denied attempts visually highlighted for review.
The API Audit panel can export filtered authorization events as an ORIMUS API Audit Package JSON file.
The Mission Replay panel can play, scrub, speed up, and URL-address a selected report's chronological event stream.
The dashboard header keeps a persistent readiness indicator and polls backend readiness automatically.

## ROS Mission API Bridge

The ROS-aware mission API bridge is provided by `mission_api_bridge`.

It publishes HTTP mission commands to ROS 2 `/mission/command`.

Initial bridge endpoints:

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
