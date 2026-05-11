# Project Status

Project name: ORIMUS

## Current Phase

Phase 01 - Project Foundation

## Current Status

The project architecture and phase roadmap have been drafted.

## Completed

- Created architecture reference document.
- Created project phase roadmap.
- Created separate phase documents.
- Created initial README.
- Created project status document.
- Created decision log.
- Created glossary.
- Confirmed first robot platform: Unitree Go2X.
- Confirmed first target: simulation.
- Confirmed preferred development operating system: Windows.
- Confirmed preferred development strategy: Docker-based environment.
- Installed Git for Windows.
- Installed WSL2 and Ubuntu on the user's Windows account.
- Installed Docker Desktop.
- Verified Docker by running the `hello-world` container.
- Selected ROS 2 Humble as the first development distribution.
- Added first Docker Compose development container definition.
- Added safety assumptions document.
- Added `.gitattributes` for Windows/Linux line-ending stability.
- Created initial ROS 2 workspace.
- Created `core_interfaces` ROS 2 package.
- Created `mock_go2x_driver` ROS 2 package.
- Created `safety_manager` ROS 2 package.
- Added command request safety gate flow.
- Created `orimus_bringup` ROS 2 launch package.
- Added one-command launch flow for mock Go2X plus safety manager.
- Created `mission_manager` ROS 2 package.
- Added first demo mission: stand, walk forward, stop, sit.
- Added generic payload command and result interfaces.
- Created `payload_manager` ROS 2 package.
- Created `mock_payloads` ROS 2 package with a mock inspection camera.
- Added mission YAML configuration support.
- Added first mission config: `configs/missions/demo_forward_stop.yaml`.
- Extended mission YAML steps to target either robot commands or payload commands.
- Updated the demo mission to trigger a mock inspection camera scan.
- Added mission event messages.
- Added `report_manager` ROS 2 package.
- Added JSON mission report output.
- Added mission control commands: start, pause, resume, cancel.
- Added `configs/missions/control_test.yaml`.
- Added FastAPI backend skeleton.
- Added backend endpoints for health, mission configs, and latest mission report.
- Added ROS-aware mission API bridge.
- Added HTTP endpoints that publish mission commands to `/mission/command`.
- Connected the plain backend API to the ROS-aware mission API bridge.
- Added backend mission command endpoints for start, pause, resume, and cancel.
- Added ROS bridge live runtime state endpoints for mission, robot, payload, perception, and safety state.
- Added backend runtime endpoints that forward live state from the ROS bridge.
- Added first operator dashboard prototype.
- Backend now serves the dashboard from `/dashboard/`.
- Added mission reset support for repeated dashboard demos without restarting ROS.
- Added live dashboard event history backed by ROS mission, perception, and safety events.
- Added latest mission report summary to the dashboard.
- Added SQLite mission audit database at `data/orimus.db`.
- Added persistent report list/detail backend endpoints.
- Added SHA-256 content hashes for finalized reports.
- Updated dashboard report panel into Mission History.
- Added sector metadata to mission YAML files for audit filtering.
- Added backend mission report filters by outcome, mission, sector, date range, perception event type, safety-event presence, and blocked-command evidence.
- Added Mission History dashboard filter controls.
- Added command-linked safety events and forward-compatible perception evidence artifact fields.
- Added unified dashboard audit timeline and report detail drilldowns.
- Added JSON-only ORIMUS Evidence Package export with schema v1.0 and export-level SHA-256 hash.
- Added evidence package verifier with standard exit codes and semantic consistency checks.
- Added development-mode operator identity propagation from dashboard/backend through ROS commands, safety events, and reports.
- Added operator-to-API mission command policy gate with 403 denials and backend audit logs.
- Added append-only backend audit table for allowed and denied protected API decisions with query filters.
- Added dashboard API Audit browsing with filters and distinct denied-attempt treatment.
- Logged API Audit export and verifier parity as a deferred future ticket.

## In Progress

- Project foundation planning.
- GitHub and repository setup preparation.

## Next Recommended Steps

1. Confirm the first mission scenario.
2. Confirm the first payload or sensor.
3. Define the first real mission scenario.
4. Add payload-specific adapter specifications.
5. Add dashboard/operator control planning.
6. Add API Audit JSON export and verifier support when audit handoff workflows need parity with Mission History.

## Open Questions

- Which ROS 2 distribution should be selected?
- What is the first real-world mission scenario?
- What is the first mounted payload?
- What should be the first mission scenario?
- What should be the first mounted payload or simulated payload?
