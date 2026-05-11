#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evidence_bundle import verify_evidence_bundle  # noqa: E402
from app.evidence_verifier import VerificationResult  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ZIP ORIMUS Evidence Bundle."
    )
    parser.add_argument("bundle_path", help="Path to an evidence bundle ZIP file.")
    args = parser.parse_args()

    return print_result(verify_evidence_bundle(Path(args.bundle_path)))


def print_result(result: VerificationResult) -> int:
    if result.valid:
        print("VALID: ORIMUS evidence bundle verified")
    else:
        print("INVALID: ORIMUS evidence bundle verification failed")
        for error in result.errors:
            print(f"- {error}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
