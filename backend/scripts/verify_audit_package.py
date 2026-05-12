#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.audit_package import verify_api_audit_package  # noqa: E402
from app.evidence_verifier import EXIT_SCHEMA_MISMATCH, VerificationResult  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a JSON ORIMUS API Audit Package, not a mission Evidence Package."
    )
    parser.add_argument("package_path", help="Path to an API audit package JSON file.")
    args = parser.parse_args()

    try:
        package = json.loads(Path(args.package_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return print_result(
            VerificationResult(False, EXIT_SCHEMA_MISMATCH, [f"unreadable JSON: {error}"])
        )

    return print_result(verify_api_audit_package(package))


def print_result(result: VerificationResult) -> int:
    if result.valid:
        print("VALID: ORIMUS API audit package verified")
    else:
        print("INVALID: ORIMUS API audit package verification failed")
        for error in result.errors:
            print(f"- {error}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
