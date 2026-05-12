#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mission_schema import validate_mission_directory  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ORIMUS mission YAML files.")
    parser.add_argument(
        "mission_dir",
        nargs="?",
        default="/workspace/configs/missions",
        help="Directory containing mission YAML files.",
    )
    args = parser.parse_args()

    try:
        missions = validate_mission_directory(Path(args.mission_dir))
    except ValueError as error:
        print(f"INVALID: {error}")
        return 1

    print(f"VALID: {len(missions)} mission configs verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
