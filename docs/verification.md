# Verification

ORIMUS uses Docker-first verification so the host machine stays clean and Windows setup remains simple.

## Confidence Button

Run the main project verification command from PowerShell:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

Default mode is fail-fast. It stops at the first failed check and exits non-zero.

Use `--all` when debugging and you want every check to run before seeing the summary:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh --all
```

Each check prints timing:

```text
[PASS] backend API tests (3.2s)
[PASS] mission YAML validation (0.4s)
SUMMARY: 3 passed, 0 failed
```

## What To Run Before A Commit

Recommended minimum:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

Also run the full scenario harness when changes touch mission sequencing, safety behavior, payload flow, ROS launch files, report generation, or scenario expectations:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh --all"
```

That gives a practical split:

- backend/dashboard/docs/API changes: `verify_project.sh`
- mission/safety/payload/ROS behavior changes: `verify_project.sh` plus `run_scenario_check.sh --all`

## Current Checks

`scripts/verify_project.sh` currently runs:

- backend API test suite
- mission YAML validation
- OpenAPI drift check against `docs/openapi.json`

The backend API suite also covers:

- dashboard static contract checks
- mission schema validation
- scenario manifest parsing
- evidence package verification
- evidence bundle verification
- readiness endpoint behavior
- backend audit behavior
- report, artifact, replay, and export behavior

## Interpreting Failures

Fail-fast mode prints the failing check output immediately and stops.

`--all` mode prints every check result, then a final summary:

```text
SUMMARY: 2 passed, 1 failed
FAILED: OpenAPI drift check
```

If the OpenAPI drift check fails, regenerate the spec:

```powershell
docker compose run --rm backend bash -lc "PYTHONPATH=backend python backend/scripts/regenerate_api_spec.py"
```

If mission validation fails, inspect the YAML file named in the error and compare it with `configs/mission_schema.json`.

If backend tests fail, read the first pytest failure and fix that behavior before rerunning.
