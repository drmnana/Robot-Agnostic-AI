#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scenario_manifest import find_scenario, load_scenario_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an ORIMUS scenario result.")
    parser.add_argument("scenario_id")
    parser.add_argument("--manifest", default="/workspace/configs/scenarios.yaml")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    try:
        manifest = load_scenario_manifest(Path(args.manifest))
        scenario = find_scenario(manifest, args.scenario_id)
        if scenario.is_backend_policy_scenario:
            print(f"PASS: scenario {scenario.id} is backend-policy-only")
            return 0
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        failures = evaluate_report(scenario, report)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: scenario {args.scenario_id} could not be checked: {error}")
        return 1

    if failures:
        for failure in failures:
            print(failure)
        return 1

    report_id = report.get("report_id", "unknown-report")
    print(f"PASS: scenario {scenario.id} met expectations, see report {report_id}")
    return 0


def evaluate_report(scenario, report: dict) -> list[str]:
    expected = scenario.expected
    report_id = report.get("report_id", "unknown-report")
    failures = []
    mission = report.get("mission") or {}
    checks = [
        ("outcome", expected.outcome, mission.get("state")),
        ("min_mission_events", expected.min_mission_events, len(report.get("mission_events", []))),
        ("min_robot_commands", expected.min_robot_commands, len(report.get("robot_commands", []))),
        ("min_payload_results", expected.min_payload_results, len(report.get("payload_results", []))),
        ("min_perception_events", expected.min_perception_events, len(report.get("perception_events", []))),
    ]
    for name, expected_value, observed_value in checks:
        if name.startswith("min_"):
            if observed_value < expected_value:
                failures.append(
                    format_failure(scenario.id, name, f">= {expected_value}", observed_value, report_id)
                )
        elif observed_value != expected_value:
            failures.append(
                format_failure(scenario.id, name, expected_value, observed_value, report_id)
            )

    artifact_count = sum(
        1 for event in report.get("perception_events", []) if event.get("evidence_artifact_url")
    )
    if expected.artifact_required and artifact_count == 0:
        failures.append(
            format_failure(scenario.id, "artifact_required", "at least 1 artifact", artifact_count, report_id)
        )

    safety_count = len(report.get("safety_events", []))
    if expected.safety_event_required and safety_count == 0:
        failures.append(
            format_failure(scenario.id, "safety_event_required", "at least 1 safety event", safety_count, report_id)
        )

    return failures


def format_failure(scenario_id: str, expectation: str, expected, observed, report_id: str) -> str:
    return (
        f"FAIL: scenario {scenario_id} expectation {expectation} "
        f"expected {expected}, observed {observed}, see report {report_id}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
