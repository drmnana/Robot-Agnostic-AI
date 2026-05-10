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

## In Progress

- Project foundation planning.
- GitHub and repository setup preparation.

## Next Recommended Steps

1. Confirm the first mission scenario.
2. Confirm the first payload or sensor.
3. Define the first real mission scenario.
4. Add mission start, pause, resume, and cancel controls.
5. Add payload-specific adapter specifications.
6. Add mission result summaries.

## Open Questions

- Which ROS 2 distribution should be selected?
- What is the first real-world mission scenario?
- What is the first mounted payload?
- What should be the first mission scenario?
- What should be the first mounted payload or simulated payload?
