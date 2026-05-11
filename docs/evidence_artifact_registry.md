# Evidence Artifact Registry

## Purpose

The artifact registry stores references to evidence files created during missions.

It is intentionally generic. A future camera frame, chemical scan, vibration trace, thermal image, or other payload output should all fit without changing the registry contract.

## Storage

Artifact files are stored under:

```text
/workspace/data/artifacts
```

Artifact metadata is stored in the same SQLite database as mission reports:

```text
/workspace/data/orimus.db
```

Table:

```text
evidence_artifacts
```

## Schema v1

Required fields only:

- `artifact_id`
- `mission_id`
- `report_id`
- `source`
- `artifact_type`
- `file_path`
- `sha256_hash`
- `created_at`
- `metadata_json`

`source` and `artifact_type` are free-form strings.

`metadata_json` is an opaque JSON blob. The registry stores it but does not validate its shape.

## API

```text
GET /artifacts
GET /artifacts/{artifact_id}
GET /artifacts/{artifact_id}/download
```

`GET /artifacts` supports optional filters:

- `mission_id`
- `report_id`
- `source`
- `artifact_type`

Downloads verify the stored SHA-256 hash before returning the file.

## Current Mock Artifact

The mock inspection camera writes a minimal 1 KB text artifact with artifact type:

```text
mock-payload-stub
```

This file exists only to prove end-to-end artifact plumbing. It is not a realistic sensor artifact format.

## Deferred Taxonomy

Artifact type taxonomy and metadata schema are deferred.

They will be defined once real perception sources are integrated.
