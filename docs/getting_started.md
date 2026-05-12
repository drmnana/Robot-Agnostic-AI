# Getting Started

This is the single entry point for running ORIMUS locally.

## 1. Clone The Repository

```powershell
git clone https://github.com/drmnana/Robot-Agnostic-AI.git
cd Robot-Agnostic-AI
```

If the repository is already cloned with GitHub Desktop, open PowerShell in that repository folder.

## 2. Confirm Requirements

ORIMUS is Docker-first. The host machine only needs:

- Git for Windows or GitHub Desktop
- Docker Desktop
- WSL2 enabled for Docker Desktop

You do not need to install ROS 2 directly on Windows for the current simulation-first workflow.

## 3. Build And Start The Local Services

```powershell
docker compose up -d --build backend ros2-dev
```

The backend serves the dashboard at:

```text
http://localhost:8000/dashboard/
```

The ROS 2 development container is available as the `ros2-dev` service. Some scenario checks start ROS launch processes inside this service.

## 4. Run The Confidence Button

Before making a commit or before a demo, run:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

This is the main ORIMUS confidence button. It runs in fail-fast mode by default.

When debugging and you want every check to run before the final summary:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh --all
```

Run the full scenario harness when changes touch mission sequencing, safety behavior, payload flow, ROS launch files, report generation, or scenario expectations:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && scripts/run_scenario_check.sh --all"
```

## 5. Restart Modes

Use a soft restart when recovering from an error and you want to preserve mission history, artifacts, and backend audit data:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --soft
```

Use a hard restart when preparing a clean demo and you intentionally want to wipe local demo history:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --hard
```

Hard restart deletes only:

- `data/orimus.db`
- `data/artifacts`
- `reports/latest_mission_report.json`

It does not delete source code, configs, docs, Dockerfiles, or mission YAML.

## 6. What To Expect

When only the backend is running, historical reports, exports, readiness, and dashboard pages should work.

If the ROS mission API bridge is not running, the dashboard may show the runtime stream or readiness as degraded. That is expected: ORIMUS can still browse existing audit history, but live robot runtime data is unavailable.

## 7. Where To Go Next

- [Troubleshooting](troubleshooting.md)
- [Verification](verification.md)
- [Dashboard Operator Workflow](dashboard_operator_workflow.md)
- [Backend Health And Readiness](backend_health_readiness.md)
- [Scenario Test Harness](scenario_test_harness.md)
- [Current Architecture Snapshot](current_architecture_snapshot.md)
- [CTO Review Items](cto_review_items.md)
