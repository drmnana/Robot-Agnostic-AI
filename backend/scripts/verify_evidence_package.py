#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evidence_verifier import (  # noqa: E402
    EXIT_SCHEMA_MISMATCH,
    VerificationResult,
    verify_evidence_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a JSON ORIMUS Evidence Package."
    )
    parser.add_argument("package_path", help="Path to an evidence package JSON file.")
    args = parser.parse_args()

    try:
        package = json.loads(Path(args.package_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return print_result(
            VerificationResult(False, EXIT_SCHEMA_MISMATCH, [str(error)])
        )

    return print_result(verify_evidence_package(package))


def print_result(result: VerificationResult) -> int:
    if result.valid:
        print("VALID: ORIMUS evidence package verified")
    else:
        print("INVALID: ORIMUS evidence package verification failed")
        for error in result.errors:
            print(f"- {error}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
