# CTO Review Items

This document pins architecture decisions that should wait for CTO guidance.

ORIMUS can continue advancing simulation, audit, dashboard, mission configuration, and software quality without these decisions. Real robot and real payload integration should remain deferred until these items are reviewed.

## 1. Real Robot Platform Integration

Status: Deferred for CTO.

Current mock implementation:

- `mock_go2x_driver` publishes robot state and accepts approved robot commands.
- `safety_manager` gates requested robot commands before they reach the mock driver.
- `mission_api_bridge` exposes HTTP mission commands and runtime state from inside ROS 2.
- Mission commands currently use generic ROS 2 messages in `core_interfaces`.

CTO decisions needed:

- Confirm first real platform target and exact model variant.
- Confirm vendor SDK/API path and ROS 2 compatibility strategy.
- Define which commands are allowed in early hardware tests.
- Define hardware-level emergency stop, manual override, and operator authority rules.
- Define platform adapter boundaries and capability discovery expectations.
- Confirm networking, DDS, and deployment topology for the robot.

Integration seam:

```text
ORIMUS mission/safety layer
        |
        v
robot command request / approved command / robot state contracts
        |
        v
platform adapter
        |
        v
vendor SDK, robot ROS driver, or hardware API
```

Today, the platform adapter role is filled by `mock_go2x_driver`.

## 2. Real Payload Integration

Status: Deferred for CTO.

Current mock implementation:

- `payload_manager` gates payload command requests.
- `mock_inspection_camera` accepts generic payload commands.
- The mock payload emits `PayloadResult` and `PerceptionEvent`.
- The mock payload writes a minimal `mock-payload-stub` artifact only to prove artifact plumbing.
- `report_manager` persists payload results, perception events, artifact references, and mission reports.

CTO decisions needed:

- Confirm first real payload or payload kit.
- Confirm hardware interface: USB, Ethernet, serial, vendor API, ROS driver, or custom service.
- Define calibration, arming, health, and safe shutdown requirements.
- Define artifact formats and retention requirements.
- Define metadata taxonomy for real artifacts.
- Define legal/privacy restrictions for camera, face recognition, audio, or biometric workflows.

Integration seam:

```text
ORIMUS mission/payload manager
        |
        v
payload command / payload state / payload result / perception event contracts
        |
        v
payload adapter
        |
        v
sensor hardware, vendor SDK, perception model, or acquisition service
```

Today, the payload adapter role is filled by `mock_inspection_camera`.

## 3. Deferred Taxonomy And Hardware Rules

The following should not be finalized until real platform and payload choices are reviewed:

- Robot capability taxonomy
- Payload type taxonomy
- Artifact metadata schema
- Real evidence file formats
- Hardware safety limits
- Real-world geofencing behavior
- Real robot deployment checklist
- Real payload calibration workflow

## Work That Can Continue Without CTO

- Simulation scenario library
- Mission YAML validation
- Scenario test harness
- Dashboard usability improvements
- Backend API documentation
- Audit/export/replay hardening
- Mock autonomy planner skeleton
- CI and repeatable verification scripts
