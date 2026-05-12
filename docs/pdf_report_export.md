# PDF Report Export

ORIMUS can export a human-readable PDF summary for a mission report:

```text
GET /reports/{report_id}/export-pdf
```

The PDF is a presentation artifact. The authoritative machine-readable record remains the JSON Evidence Package from:

```text
GET /reports/{report_id}/export
```

## Integrity Disclosure

The first page includes this disclosure:

```text
This PDF is a human-readable summary. The authoritative machine-readable record is the JSON Evidence Package (SHA-256: <hash>). To verify integrity, retrieve the JSON package and run verify_evidence_package.py.
```

Every page footer includes:

- report ID
- JSON Evidence Package SHA-256 hash
- page number

This keeps extracted, printed, scanned, or out-of-order pages tied back to the authoritative JSON export.

## Included Content

The PDF includes:

- report ID
- mission ID/name/sector/outcome
- generated timestamp
- mission report content hash
- JSON Evidence Package SHA-256 hash
- event counts
- severity-labeled timeline
- command, safety, perception, and payload summaries
- artifact references and hashes when present

## Generator Choice

ORIMUS currently uses a small internal standard-library PDF generator in `backend/app/pdf_report.py`.

Tradeoff:

- Chosen now: no extra Docker system dependencies, reliable in the slim Python backend image, simple CI/build behavior.
- Deferred: richer HTML/CSS rendering through WeasyPrint.

WeasyPrint would allow more polished HTML/CSS layouts and reuse of dashboard styling, but it requires Cairo/Pango system dependencies in the backend Docker image. That is a good future upgrade when PDF branding/layout becomes a dedicated design ticket.

ReportLab and fpdf2 were not chosen for this ticket because they add dependency management without materially changing the current summary layout needs.

## Verification Boundary

There is no PDF verifier in this ticket.

To verify integrity, export the JSON Evidence Package and run:

```powershell
docker compose run --rm backend python backend/scripts/verify_evidence_package.py path/to/evidence-package.json
```
