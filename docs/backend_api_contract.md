# Backend API Contract

This document describes the current ORIMUS FastAPI backend contract for operators, dashboard code, tooling, and reviewers.

Machine-readable OpenAPI is committed at [openapi.json](openapi.json).
Interactive exploration is available from a running backend at:

```text
http://localhost:8000/docs
```

Regenerate the committed OpenAPI artifact with:

```powershell
docker compose run --rm backend bash -lc "PYTHONPATH=backend python backend/scripts/regenerate_api_spec.py"
```

## Operator Identity And Policy

`X-ORIMUS-Operator` is development-mode attribution only. It is self-asserted and is not authentication.

Production deployment requires real authentication and non-repudiation, such as JWT, mTLS, SSO, or another CTO-approved identity layer.

Current policy levels from `configs/operator_policy.yaml`:

- `anonymous`: `pause`
- `operator-demo`: `start`, `pause`, `resume`, `reset`
- `supervisor-demo`: `start`, `pause`, `resume`, `cancel`, `reset`
- `none`: endpoint is not protected by operator policy

Operator-to-API authorization does not replace, augment, or coordinate with the ROS `safety_manager` or any hardware-level safety constraint.

## Health

### `GET /health`

Purpose: legacy lightweight backend health response.

Policy: `none`.

Request: no params, headers, or body.

Response: `200` with backend status and service name.

Status codes:

- `200`: backend answered.

### `GET /healthz`

Purpose: liveness endpoint for deployment orchestrators. It only proves the backend process is responsive.

Policy: `none`.

Request: no params, headers, or body.

Response: `200` with `status: alive` and service name.

Status codes:

- `200`: backend process is responsive.

### `GET /readiness`

Purpose: operator pre-flight readiness. Validates required backend dependencies and optional ROS bridge availability.

Policy: `none`.

Query params:

- `fresh`: boolean, optional. When `true`, bypasses the 10-second expensive-check cache.

Response: readiness summary with overall `status`, cache metadata, and per-check records. Each check includes `requirement` and normalized event `severity`.

Status codes:

- `200`: readiness report returned. Overall readiness is expressed inside the JSON body.

## Missions

### `GET /missions`

Purpose: list configured mission YAML files for dashboard selection.

Policy: `none`.

Request: no params, headers, or body.

Response: `missions` array with `mission_id`, `name`, `sector`, source `path`, and `step_count`.

Status codes:

- `200`: missions listed.

### `GET /missions/{mission_id}`

Purpose: return one mission YAML file as JSON.

Policy: `none`.

Path params:

- `mission_id`: mission YAML stem.

Response: mission configuration document.

Status codes:

- `200`: mission found.
- `404`: mission config not found.

### `POST /missions/{mission_id}/{command_type}`

Purpose: send an operator mission command through the backend to the ROS-aware mission API bridge.

Policy:

- `pause`: `anonymous`, `operator-demo`, `supervisor-demo`
- `start`: `operator-demo`, `supervisor-demo`
- `resume`: `operator-demo`, `supervisor-demo`
- `reset`: `operator-demo`, `supervisor-demo`
- `cancel`: `supervisor-demo`

Headers:

- `X-ORIMUS-Operator`: optional development-mode operator ID. Blank or missing becomes `anonymous`.

Path params:

- `mission_id`
- `command_type`: `start`, `pause`, `resume`, `cancel`, or `reset`

Response: accepted command response from the ROS mission API bridge, including mission and operator context.

Audit behavior:

- Allowed and denied attempts are written to the backend API audit log.
- Denied attempts are rejected before ROS forwarding.

Status codes:

- `200`: command accepted by backend and bridge.
- `400`: unsupported command type.
- `403`: operator policy denied the request.
- `502`: bridge returned an unexpected HTTP error.
- `503`: bridge unavailable.
- `504`: bridge request timed out.

## Runtime

### `GET /runtime/{resource}`

Purpose: read live runtime state proxied from the ROS mission API bridge.

Policy: `none`.

Path params:

- `resource`: `state`, `mission`, `robot`, `payload`, `perception`, `safety`, or `events`

Response: resource-specific runtime JSON from the bridge.

Status codes:

- `200`: runtime resource returned.
- `400`: unsupported runtime resource.
- `502`: bridge returned an unexpected HTTP error.
- `503`: bridge unavailable.
- `504`: bridge request timed out.

### `GET /runtime/stream`

Purpose: read-only Server-Sent Events stream for live dashboard runtime updates.

Policy: `none`.

Event types:

- `runtime_state`
- `readiness`
- `heartbeat`
- `runtime_error`

Response: `text/event-stream`.

Status codes:

- `200`: stream opened.

## Reports

### `GET /reports`

Purpose: browse persisted mission report summaries.

Policy: `none`.

Query params:

- `outcome`
- `mission_id`
- `sector`
- `date_from`: Unix seconds
- `date_to`: Unix seconds
- `perception_event_type`
- `has_safety_event`
- `command_blocked`

Response: `reports` array with report IDs, mission metadata, outcome, timestamps, event counts, and content hashes.

Status codes:

- `200`: reports listed.

### `GET /reports/{report_id}`

Purpose: return full persisted mission report detail.

Policy: `none`.

Path params:

- `report_id`

Response: full mission report JSON.

Status codes:

- `200`: report found.
- `404`: report not found.

### `GET /reports/latest`

Purpose: return the latest JSON mission report file for backward-compatible dashboard/demo reads.

Policy: `none`.

Request: no params, headers, or body.

Response: latest mission report JSON.

Status codes:

- `200`: latest report found.
- `404`: latest mission report file not found.

### `GET /reports/{report_id}/export`

Purpose: export an ORIMUS Evidence Package JSON file for a mission report.

Policy: `none`.

Path params:

- `report_id`

Response: JSON Evidence Package Schema v1.0 with export-level SHA-256 hash.

Status codes:

- `200`: package returned.
- `404`: report not found.

### `GET /reports/{report_id}/export-bundle`

Purpose: export a deterministic ZIP evidence bundle containing the evidence package, manifest, and referenced artifact files.

Policy: `none`.

Path params:

- `report_id`

Response: `application/zip` evidence bundle.

Status codes:

- `200`: bundle returned.
- `404`: report or referenced artifact file not found.

### `GET /reports/{report_id}/export-pdf`

Purpose: export a human-readable PDF summary for a mission report.

Policy: `none`.

Path params:

- `report_id`

Response: `application/pdf` mission report summary. The PDF includes the JSON Evidence Package SHA-256 hash in the first-page disclosure and every page footer.

Status codes:

- `200`: PDF returned.
- `404`: report not found.

### `GET /reports/{report_id}/replay`

Purpose: return normalized chronological replay frames for mission review.

Policy: `none`.

Path params:

- `report_id`

Query params:

- `category`
- `since`: Unix seconds
- `operator_id`
- `command_id`

Response: `report_id`, `frame_count`, and sorted `frames`.

Status codes:

- `200`: replay frames returned.
- `404`: report not found.

## Artifacts

### `GET /artifacts`

Purpose: browse registered evidence artifacts.

Policy: `none`.

Query params:

- `mission_id`
- `report_id`
- `source`
- `artifact_type`

Response: `artifacts` array with artifact ID, mission/report IDs, source, artifact type, file path, hash, creation time, and opaque metadata.

Status codes:

- `200`: artifacts listed.

### `GET /artifacts/{artifact_id}`

Purpose: return one artifact registry record.

Policy: `none`.

Path params:

- `artifact_id`

Response: artifact metadata record.

Status codes:

- `200`: artifact found.
- `404`: artifact not found.

### `GET /artifacts/{artifact_id}/download`

Purpose: download an artifact file after hash verification.

Policy: `none`.

Path params:

- `artifact_id`

Response: `application/octet-stream` artifact bytes.

Status codes:

- `200`: artifact file returned.
- `404`: artifact not found.
- `409`: artifact hash mismatch.

## API Audit

### `GET /audit/events`

Purpose: browse backend operator authorization audit events.

Policy: `none` for current development dashboard browsing.

Query params:

- `operator_id`
- `decision`: `allowed` or `denied`
- `event_type`
- `date_from`: Unix seconds
- `date_to`: Unix seconds

Response: `events` array with operator ID, decision, mission ID, command type, request path, optional source IP, reason, retention class, normalized severity, and timestamp.

Status codes:

- `200`: audit events listed.

### `GET /audit/events/export`

Purpose: export filtered backend authorization audit events as an ORIMUS API Audit Package JSON file.

Policy: `none` for current development dashboard export.

Query params:

- `operator_id`
- `decision`: `allowed` or `denied`
- `event_type`
- `date_from`: Unix seconds
- `date_to`: Unix seconds

Response: JSON API Audit Package Schema v1.0 with export-level SHA-256 hash.

Status codes:

- `200`: audit package returned.

### `GET /audit/events/export-bundle`

Purpose: export filtered backend authorization audit events as a deterministic ORIMUS API Audit Bundle ZIP file.

Policy: `none` for current development dashboard export.

Query params:

- `operator_id`
- `decision`: `allowed` or `denied`
- `event_type`
- `date_from`: Unix seconds
- `date_to`: Unix seconds

Response: `application/zip` API Audit Bundle Schema v1.0 containing `api_audit_package.json` and `manifest.json`.

Status codes:

- `200`: audit bundle returned.

## Deferred / Not Yet Stable

These contract areas are intentionally marked as likely to evolve:

- `GET /runtime/robot`: robot pose, mode, battery, and platform fields are mock-Go2X oriented today. They may change when the CTO approves the real `RobotInterface` abstraction and platform adapters.
- `GET /runtime/payload`: payload state fields are generic today. Real payload health, arming, calibration, and fault fields are deferred until real payload integration.
- `GET /runtime/perception`: current perception state is mock-camera oriented. Real model output fields, confidence semantics, and class taxonomies are deferred pending perception model selection.
- `perception_events.evidence_artifact_url` and `evidence_hash`: these fields exist now, but artifact URL format and evidence metadata are deferred until real perception and payload sources are integrated.
- Artifact `artifact_type`, `source`, and `metadata_json`: deliberately free-form until the CTO reviews real payload artifact taxonomy.
- Mission YAML step fields for robot movement: current `walk_velocity` parameters support the simulation path. Real robot command payloads may change if the platform adapter introduces richer command contracts.
- Mission command bridge responses: current responses mirror the ROS mission API bridge. They may be normalized later if multiple platform adapters require a stricter backend envelope.
- Authentication: `X-ORIMUS-Operator` is development-mode attribution only. Production auth is deferred.
