# Simulation Scenario Library

The scenario library gives ORIMUS repeatable simulated missions that exercise mission sequencing, safety, payload artifacts, operator controls, and backend governance without real robot or real payload assumptions.

## Mission YAML Schema

The mission contract is defined in:

```text
configs/mission_schema.json
```

The schema is generated from the Pydantic model in:

```text
backend/app/mission_schema.py
```

Mission configs are validated by:

```text
backend/scripts/validate_missions.py
```

The backend pytest suite validates every YAML file in `configs/missions` on each run.

## Scenarios

### `demo_forward_stop.yaml`

Baseline demonstration mission.

Proves:

- robot command sequencing
- payload scan step
- mission report generation
- artifact-capable perception event flow

### `control_test.yaml`

Longer control mission used by pause, resume, cancel, and reset smoke flows.

Proves:

- operator control path
- repeated dashboard demos
- mission state transitions

### `perimeter_patrol.yaml`

Simulated patrol loop with straight motion and turn steps.

Proves:

- multi-step robot motion sequencing
- report timeline readability across repeated movement

### `artifact_inspection.yaml`

Simulated inspection that triggers the mock inspection camera.

Proves:

- payload command path
- mock artifact creation
- report-to-artifact linkage
- evidence bundle inclusion

### `safety_speed_limit.yaml`

Simulated mission that requests speed above the configured safety limit.

Proves:

- safety manager clamping/intervention behavior
- safety events in reports and replay

### `pause_resume_training.yaml`

Longer mission for operator pause and resume practice.

Proves:

- dashboard command timing
- mission pause and resume behavior

### `policy_denial_demo.yaml`

Backend governance scenario.

The scenario is designed to pair with an anonymous `cancel` request. Anonymous operators are not allowed to cancel missions, so the backend should return `403` and record a denied backend audit event before any ROS forwarding.

Proves:

- operator-to-API authorization
- denied-command audit trail
- governance behavior independent from robot safety
