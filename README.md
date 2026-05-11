# ORIMUS

ORIMUS is a robot-agnostic autonomous AI mission system for quadruped robot platforms such as Unitree Go2, Unitree B2, Boston Dynamics Spot, Ghost Robotics platforms, and future ROS 2-compatible robots.

The project is currently in the planning and foundation stage.

## Project Documents

- [Architecture Reference](docs/architecture_reference.md)
- [Project Phase Roadmap](docs/project_phase_roadmap.md)
- [Project Status](docs/project_status.md)
- [Decision Log](docs/decision_log.md)
- [Glossary](docs/glossary.md)
- [Docker Environment](docs/docker_environment.md)
- [Safety Assumptions](docs/safety_assumptions.md)
- [Evidence Package Schema v1.0](docs/evidence_package_schema_v1.md)
- [Evidence Package Verification](docs/evidence_package_verification.md)

## Current Phase

Phase 01 - Project Foundation

## Immediate Goals

- Prepare a Windows-friendly simulation-first development setup.
- Create and upload the initial project package to GitHub.
- Confirm the first mission scenario.
- Confirm the first payload or sensor.
- Set up Git and GitHub.
- Define safety rules for version 1.

## Current Direction

- First robot platform: Unitree Go2X
- First development target: simulation
- Preferred host operating system: Windows
- Preferred development strategy: Docker-based environment

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

The first configurable mission is:

- `configs/missions/demo_forward_stop.yaml`
- `configs/missions/control_test.yaml`

Mission steps can target either `robot` or `payload`.
Mission YAML metadata includes a `sector` field so reports can be filtered by operating area.

## Backend

The first backend skeleton is located in `backend/`.

Initial endpoints:

- `GET /health`
- `GET /missions`
- `GET /missions/{mission_id}`
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
- `GET /reports`
- `GET /reports/{report_id}/export`
- `GET /reports/latest`
- `GET /reports/{report_id}`

Mission command endpoints forward operator requests to the ROS-aware mission API bridge.
Runtime endpoints forward live state reads from the ROS-aware mission API bridge.
The bridge URL is configured with `ORIMUS_MISSION_API_BRIDGE_URL`.

`GET /reports` supports audit filters for `outcome`, `mission_id`, `sector`, `date_from`, `date_to`, `perception_event_type`, `has_safety_event`, and `command_blocked`.
`GET /reports/{report_id}/export` returns a JSON-only ORIMUS Evidence Package using schema version `1.0` with an export-level SHA-256 hash.

## Operator Dashboard

The first operator dashboard prototype is located in `dashboard/` and is served by the backend.

Open it at:

```text
http://localhost:8000/dashboard/
```

The dashboard can list missions, send mission commands, reset missions for repeated demos, display live runtime state, show mission event history, and browse/filter persisted mission reports from the backend.

Mission reports are persisted to SQLite at `data/orimus.db` inside the workspace mount.
Each finalized report is stored with a SHA-256 content hash for audit traceability.
Report detail views show a unified chronological audit timeline, command safety verdicts, safety-event command links, perception evidence metadata, payload results, and report integrity fields.
Selected reports can be exported as JSON evidence packages.
Evidence packages can be verified with `backend/scripts/verify_evidence_package.py`.

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
