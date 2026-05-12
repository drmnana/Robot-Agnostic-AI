#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.audit_bundle import verify_api_audit_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a ZIP ORIMUS API Audit Bundle, not a mission Evidence Bundle."
    )
    parser.add_argument("bundle_path", help="Path to an API audit bundle ZIP file.")
    args = parser.parse_args()

    return print_result(verify_api_audit_bundle(Path(args.bundle_path)))


def print_result(result) -> int:
    if result.valid:
        print("VALID: ORIMUS API audit bundle verified")
    else:
        print("INVALID: ORIMUS API audit bundle verification failed")
        for error in result.errors:
            print(f"- {error}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
