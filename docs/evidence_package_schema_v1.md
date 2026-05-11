# ORIMUS Evidence Package Schema v1.0

## Purpose

An ORIMUS Evidence Package is a JSON-only export of one finalized mission report for audit review, archival, or handoff.

Schema versions are stable contracts. Future schema versions may add fields, but they must not break the meaning of fields defined in v1.0.

## Package Rules

- File format: JSON.
- Schema version: `1.0`.
- One package contains one mission report.
- `export_hash` is a SHA-256 hash of the canonical JSON package with `export_hash` set to an empty string.
- `report.content_hash` is the mission report hash created at mission finalization.
- `export_hash` is separate from `report.content_hash` and verifies the downloaded package itself.
- Evidence artifacts are represented in `artifact_manifest`; binary files are not embedded in v1.0.

## Top-Level Fields

```json
{
  "package_type": "orimus_evidence_package",
  "schema_version": "1.0",
  "generated_at": "2026-05-11T00:00:00+00:00",
  "export_hash_algorithm": "SHA-256",
  "export_hash": "sha256-of-package",
  "report": {},
  "mission": {},
  "artifact_manifest": [],
  "mission_report": {}
}
```

## `report`

```json
{
  "report_id": "orimus-report-id",
  "content_hash": "sha256-of-finalized-mission-report",
  "content_hash_algorithm": "SHA-256"
}
```

## `mission`

```json
{
  "mission_id": "demo_forward_stop",
  "name": "Demo Forward Stop",
  "sector": "training-yard-alpha",
  "outcome": "completed",
  "started_at": {"sec": 0, "nanosec": 0},
  "ended_at": {"sec": 0, "nanosec": 0}
}
```

## `artifact_manifest`

Each artifact entry describes a future evidence artifact referenced by a perception event.

```json
{
  "source_event_id": "perception-event-id",
  "event_type": "person_detected",
  "source": "inspection_camera_001",
  "artifact_url": null,
  "artifact_hash": null,
  "artifact_hash_algorithm": null
}
```

When an artifact exists, `artifact_hash_algorithm` must be `SHA-256`.

## `mission_report`

`mission_report` contains the full finalized ORIMUS mission report exactly as stored by the backend.

## Hash Verification

To verify `export_hash`:

1. Parse the JSON package.
2. Save the current `export_hash` value.
3. Set `export_hash` to an empty string.
4. Serialize the package with sorted keys and compact separators.
5. Compute SHA-256 over the serialized UTF-8 bytes.
6. Compare the result to the saved `export_hash`.
