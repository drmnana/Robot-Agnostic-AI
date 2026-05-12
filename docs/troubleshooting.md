# Troubleshooting

This guide covers local Docker-first demo and development failures.

## Docker Is Not Running

Symptom:

- `docker compose ...` fails before ORIMUS starts.
- PowerShell reports that it cannot connect to the Docker daemon.

Fix:

1. Open Docker Desktop.
2. Wait until Docker Desktop says it is running.
3. In PowerShell, run:

```powershell
docker ps
```

4. Then rerun the confidence button:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

Validated check:

- `docker ps` must return successfully before any ORIMUS container command can work.

## Dashboard Opens But Runtime Is Degraded

Symptom:

- `http://localhost:8000/dashboard/` opens.
- Readiness or the stream status reports degraded.
- Runtime panels mention the ROS mission API bridge.

Fix:

1. Confirm containers are up:

```powershell
docker compose ps
```

2. Soft restart ORIMUS services:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --soft
```

3. Force a fresh readiness check:

```text
http://localhost:8000/readiness?fresh=true
```

Validated check:

- The backend readiness tests exercise the ROS bridge unavailable path and confirm ORIMUS degrades instead of failing the whole dashboard.

## Mission YAML Or Config Is Invalid

Symptom:

- Readiness reports `mission_yaml_validation` as `not_ready`.
- `verify_project.sh` fails during mission YAML validation.

Fix:

1. Run the mission validator:

```powershell
docker compose run --rm backend python backend/scripts/validate_missions.py
```

2. Open the YAML file named by the error.
3. Compare it with the mission contract:

```text
configs/mission_schema.json
```

4. Rerun:

```powershell
docker compose run --rm backend bash scripts/verify_project.sh
```

Validated check:

- The backend test suite includes malformed mission YAML cases and verifies that readiness reports required config failures.

## Demo Data Is Stale Or Confusing

Symptom:

- Old mission reports, artifacts, or backend audit events make a demo hard to follow.

Fix:

Use a hard restart only when you intentionally want a clean local demo state:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/orimus_restart.ps1 --hard
```

Hard restart wipes local demo SQLite/artifact state and restarts services.

Validated check:

- Tests assert that hard restart targets only ORIMUS demo data paths and that soft restart preserves data.

## Which Restart Mode Should I Use?

Use `--soft` for:

- recovering from a local service error
- restarting backend/dashboard availability
- keeping mission history, artifacts, and audit records

Use `--hard` for:

- preparing a clean demo
- intentionally wiping local mission history
- removing old demo artifacts and audit records

When unsure, use `--soft`.
