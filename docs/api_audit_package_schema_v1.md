# API Audit Package Schema v1.0

An ORIMUS API Audit Package is a JSON-only export of backend operator authorization audit events.

This schema evolves independently from [Evidence Package Schema v1.0](evidence_package_schema_v1.md). Evidence packages describe mission reports. API audit packages describe backend API authorization decisions.

## Top-Level Fields

- `package_type`: must be `orimus_api_audit_package`
- `schema_version`: currently `1.0`
- `export_hash_algorithm`: must be `SHA-256`
- `export_hash`: SHA-256 hash of the canonical JSON package with `export_hash` set to an empty string
- `generated_at_sec`: Unix timestamp for package creation
- `filters`: export filters used to select events
- `summary`: event counts
- `events`: chronological backend audit events

## Summary

`summary` contains:

- `event_count`
- `allowed_count`
- `denied_count`

## Event Fields

Each event must include:

- `id`
- `created_at_sec`
- `event_type`
- `operator_id`
- `decision`: `allowed` or `denied`
- `request_path`
- `retention_class`

Current events may also include:

- `mission_id`
- `command_type`
- `reason`
- `source_ip`

## Verification

Use:

```powershell
docker compose run --rm backend python backend/scripts/verify_audit_package.py path/to/audit-package.json
```

The verifier checks:

- `package_type`
- `schema_version`
- `export_hash`
- event count summary
- allowed/denied count summary
- chronological timestamps
- required fields
- valid decisions

Exit codes match the ORIMUS verifier family:

- `0`: valid
- `1`: hash mismatch
- `2`: schema mismatch or unreadable JSON
- `3`: semantic failure

This verifier is only for ORIMUS API Audit Package JSON. Mission Evidence Packages must be checked with `backend/scripts/verify_evidence_package.py`.
