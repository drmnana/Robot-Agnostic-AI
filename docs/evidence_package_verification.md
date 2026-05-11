# Evidence Package Verification

## Goal

Evidence package verification confirms that a JSON ORIMUS Evidence Package is authentic to its export, matches the embedded mission report, and is internally consistent.

## Command

From the repository root:

```powershell
docker compose run --rm backend python backend/scripts/verify_evidence_package.py path/to/package.json
```

## Exit Codes

- `0`: valid package.
- `1`: hash mismatch.
- `2`: schema mismatch or unreadable JSON.
- `3`: semantic failure.

## Verification Checks

The verifier checks:

- `schema_version` is supported.
- `export_hash` matches the package JSON with `export_hash` excluded from the hash input.
- `mission_report.content_hash` matches the embedded mission report.
- `report.content_hash` matches `mission_report.content_hash`.
- Mission timestamps are monotonic within timestamped report arrays.
- Summary counts match the underlying report arrays.
- Every safety-event `command_id` resolves to a real robot command.

PDF verification is intentionally out of scope for this step.
