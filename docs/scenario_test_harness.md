# Scenario Test Harness

The scenario test harness makes ORIMUS simulation checks repeatable.

It reads the versioned contract file:

```text
configs/scenarios.yaml
```

The current manifest version is:

```text
version: 1
```

## Run One Scenario

From the repository root:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh artifact_inspection"
```

## Run All Scenarios

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh --all"
```

`--all` runs every scenario in `configs/scenarios.yaml` sequentially and prints a summary:

```text
SUMMARY: 6 passed, 0 failed
```

If any scenario fails, the runner exits non-zero and lists the failed scenario IDs.

## Debuggable Failure Output

Expectation failures include:

- scenario ID
- expectation name
- expected value
- observed value
- report ID or audit row pointer when available

Example:

```text
FAIL: scenario artifact_inspection expectation min_payload_results expected >= 1, observed 0, see report orimus-...
```

## Scenario Types

### ROS Mission Scenarios

Most scenarios launch `orimus_bringup` with a mission YAML file, wait for completion, and check the generated report.

The report checker validates expectations such as:

- final mission outcome
- minimum mission event count
- minimum robot command count
- payload result presence
- perception event presence
- artifact presence
- safety event presence

### Backend Governance Scenarios

`policy_denial_demo` is backend/API-level rather than ROS mission-level.

It verifies that an anonymous operator attempting a supervisor-level command receives `403` and that a denied backend audit event is recorded.

## Current Scenarios

- `demo_forward_stop`
- `artifact_inspection`
- `perimeter_patrol`
- `safety_speed_limit`
- `pause_resume_training`
- `policy_denial_demo`
