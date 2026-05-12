# Demo Operator Walkthrough

This walkthrough shows the current ORIMUS simulation-first system.

## Scope Of This Demo

ORIMUS today demonstrates orchestration, operator workflow, safety gating, audit persistence, evidence export, replay, and verification.

Robot movement, perception, and payload behavior are mocked:

- robot platform: `mock_go2x_driver`
- payload/perception: `mock_inspection_camera`
- real robot platform adapters: deferred for CTO review
- real payload adapters and artifact metadata: deferred for CTO review

Do not present this demo as real robot integration. Present it as the working orchestration and audit layer that real robot and payload integrations will connect to.

## Five-Minute Fast Path

Use this path when you need to show ORIMUS quickly.

1. Start clean demo services:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --hard
```

2. Run the confidence button:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

3. Run one happy-path scenario:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh artifact_inspection"
```

4. Open the dashboard:

```text
http://localhost:8000/dashboard/
```

5. Show these tabs:

- Mission Ops: live runtime/readiness context
- Mission History: latest report, timeline, artifacts, replay, JSON/bundle/PDF export buttons
- API Audit: authorization log and JSON/bundle export buttons
- System Readiness: dependency status

6. Say this clearly:

```text
The robot and payload are mocked. The demo proves ORIMUS orchestration, safety/audit structure, evidence handling, replay, and verification. Real robot and real payload contracts are intentionally deferred for CTO review.
```

## Comprehensive Walkthrough

### 1. Pre-Demo Checklist

Run from the repository root.

Check Docker:

```powershell
docker ps
```

Run the main project confidence button:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

For a clean demo state, use hard restart:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --hard
```

For recovery during a working session, use soft restart:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --soft
```

Use `--soft` when preserving mission history, artifacts, and backend audit data matters. Use `--hard` only when preparing a clean local demo.

### 2. Happy Path: Mission, Artifact, Report, Replay

Run:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh artifact_inspection"
```

Expected result:

- scenario completes
- mission report is generated
- payload result is present
- perception event is present
- evidence artifact is present

Open:

```text
http://localhost:8000/dashboard/?tab=history
```

Show:

- mission report list
- selected report integrity hash
- unified timeline
- command/safety/perception/payload panels
- artifact links
- Mission Replay controls
- Export JSON
- Export Bundle
- Export PDF

Talking point:

```text
The JSON evidence package and ZIP evidence bundle are the authoritative machine-readable records. The PDF is a human-readable summary.
```

### 3. Failure Mode: Policy Denial

Run:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh policy_denial_demo"
```

Expected result:

- anonymous operator attempts a supervisor-only command
- backend policy returns `403`
- denied authorization event is recorded

Open:

```text
http://localhost:8000/dashboard/?tab=audit
```

Show:

- denied row styling
- operator field
- command type
- request path
- filters by decision/operator
- Export JSON
- Export Bundle

Talking point:

```text
This is operator-to-API authorization. It does not replace robot safety, hardware constraints, or the ROS safety manager.
```

### 4. Failure Mode: Safety Arbitration

Run:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh safety_speed_limit"
```

Expected result:

- mission completes
- safety event is recorded
- safety arbitration appears in the mission report timeline

Open:

```text
http://localhost:8000/dashboard/?tab=history
```

Show:

- timeline safety event
- command safety verdict
- safety panel
- severity label/icon

Talking point:

```text
The safety manager is a separate ROS layer from backend authorization. Backend policy answers whether an operator may call an API. Safety arbitration answers whether a robot command should pass through the ROS safety gate.
```

### 5. Failure Mode: Degraded ROS Bridge

Stop or leave the ROS mission bridge offline, then open:

```text
http://localhost:8000/dashboard/?tab=readiness
```

Or force a fresh readiness check:

```text
http://localhost:8000/readiness?fresh=true
```

Expected result:

- backend remains available
- readiness reports degraded instead of fully ready
- historical mission/audit review remains usable
- live runtime stream may show degraded/fallback status

Talking point:

```text
ORIMUS separates historical review from live robot connectivity. Losing the bridge degrades live runtime awareness without erasing audit history.
```

Recover with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --soft
```

### 6. Failure Mode: Verifier Catches Tampering

First export a mission evidence package or bundle from Mission History.

Verify a JSON evidence package:

```powershell
docker compose run --rm backend python backend/scripts/verify_evidence_package.py path/to/evidence-package.json
```

Verify a ZIP evidence bundle:

```powershell
docker compose run --rm backend python backend/scripts/verify_evidence_bundle.py path/to/evidence-bundle.zip
```

Then edit a copied JSON package file and change one event field. Run the verifier again.

Expected result:

- valid file exits `0`
- tampered file exits non-zero
- hash mismatch or semantic failure is printed

For API audit exports:

```powershell
docker compose run --rm backend python backend/scripts/verify_audit_package.py path/to/audit-package.json
docker compose run --rm backend python backend/scripts/verify_audit_bundle.py path/to/audit-bundle.zip
```

Talking point:

```text
The verifier family is designed for custody checks: valid exports pass, altered exports fail with scriptable exit codes.
```

## Full Scenario Sweep

Run this when you want broad mock-system coverage:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh --all"
```

Expected result:

```text
SUMMARY: 6 passed, 0 failed
```

Current scenarios:

- `demo_forward_stop`
- `artifact_inspection`
- `perimeter_patrol`
- `safety_speed_limit`
- `pause_resume_training`
- `policy_denial_demo`

## Demo Close

End with:

```text
ORIMUS currently proves the simulation-first orchestration and audit foundation. The remaining architecture-defining work is real robot platform integration and real payload integration, both intentionally held for CTO review.
```
