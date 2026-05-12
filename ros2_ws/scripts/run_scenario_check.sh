#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

MANIFEST_PATH="${ORIMUS_SCENARIO_MANIFEST:-/workspace/configs/scenarios.yaml}"

usage() {
  echo "Usage: scripts/run_scenario_check.sh <scenario_id>|--all"
}

scenario_ids() {
  python3 - "$MANIFEST_PATH" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
if data.get("version") != 1:
    raise SystemExit(f"unsupported scenario manifest version {data.get('version')}; expected 1")
for scenario in data.get("scenarios", []):
    print(scenario["id"])
PY
}

scenario_field() {
  local scenario_id="$1"
  local expression="$2"
  python3 - "$MANIFEST_PATH" "$scenario_id" "$expression" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
scenario_id = sys.argv[2]
expression = sys.argv[3].split(".")
data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
if data.get("version") != 1:
    raise SystemExit(f"unsupported scenario manifest version {data.get('version')}; expected 1")
for scenario in data.get("scenarios", []):
    if scenario.get("id") == scenario_id:
        value = scenario
        for part in expression:
            value = value.get(part, {}) if isinstance(value, dict) else {}
        if isinstance(value, bool):
            print("true" if value else "false")
        elif isinstance(value, dict):
            print("")
        else:
            print(value)
        raise SystemExit(0)
raise SystemExit(f"unknown scenario '{scenario_id}'")
PY
}

run_backend_policy_scenario() {
  local scenario_id="$1"
  local command_type
  local operator_id
  local expected_status
  command_type="$(scenario_field "$scenario_id" "expected.backend_policy_denial.command_type")"
  operator_id="$(scenario_field "$scenario_id" "expected.backend_policy_denial.operator_id")"
  expected_status="$(scenario_field "$scenario_id" "expected.backend_policy_denial.status_code")"
  python3 - "$scenario_id" "$command_type" "$operator_id" "$expected_status" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, "/workspace/backend")
from app.backend_audit import BackendAuditStore  # noqa: E402
from app.operator_policy import is_mission_command_allowed  # noqa: E402

scenario_id = sys.argv[1]
command_type = sys.argv[2]
operator_id = sys.argv[3] or "anonymous"
expected_status = int(sys.argv[4])
database_path = Path("/tmp/orimus_scenario_policy.db")
if database_path.exists():
    database_path.unlink()
allowed = is_mission_command_allowed(
    Path("/workspace/configs/operator_policy.yaml"),
    operator_id,
    command_type,
)
observed_status = 200 if allowed else 403
store = BackendAuditStore(database_path)
if not allowed:
    store.record_event(
        event_type="mission_command",
        decision="denied",
        operator_id=operator_id,
        mission_id=scenario_id,
        command_type=command_type,
        reason="operator_policy",
        request_path=f"/missions/{scenario_id}/{command_type}",
        source_ip=None,
    )
events = store.list_events(operator_id=operator_id, decision="denied")
matching = [
    event for event in events
    if event["mission_id"] == scenario_id and event["command_type"] == command_type
]
if observed_status != expected_status:
    print(
        f"FAIL: scenario {scenario_id} expectation backend_policy_status "
        f"expected {expected_status}, observed {observed_status}, see backend audit rows {len(events)}"
    )
    raise SystemExit(1)
if not matching:
    print(
        f"FAIL: scenario {scenario_id} expectation denied_audit_event "
        f"expected 1 matching row, observed 0, see backend audit rows {len(events)}"
    )
    raise SystemExit(1)
print(f"PASS: scenario {scenario_id} denied {command_type} with {observed_status}, see audit row {matching[0]['id']}")
PY
}

run_ros_scenario() {
  local scenario_id="$1"
  local mission_path timeout_sec work_dir marker_path report_path db_path artifact_root log_path
  mission_path="$(scenario_field "$scenario_id" "mission_path")"
  timeout_sec="$(scenario_field "$scenario_id" "timeout_sec")"
  work_dir="/tmp/orimus_scenario_${scenario_id}"
  marker_path="${work_dir}/completed.txt"
  report_path="${work_dir}/report.json"
  db_path="${work_dir}/orimus.db"
  artifact_root="${work_dir}/artifacts"
  log_path="${work_dir}/launch.log"
  rm -rf "$work_dir"
  mkdir -p "$work_dir" "$artifact_root"

  ros2 launch orimus_bringup mock_go2x.launch.py \
    mission_autostart:=true \
    mission_config_path:="$mission_path" \
    completion_marker_path:="$marker_path" \
    report_path:="$report_path" \
    artifact_root:="$artifact_root" \
    >/tmp/orimus_scenario_launch_${scenario_id}.log 2>&1 &
  local launch_pid=$!

  cleanup_scenario() {
    kill "$launch_pid" >/dev/null 2>&1 || true
    pkill -f "mission_manager_node" >/dev/null 2>&1 || true
    pkill -f "mission_api_bridge_node" >/dev/null 2>&1 || true
    pkill -f "mock_go2x_node" >/dev/null 2>&1 || true
    pkill -f "safety_manager_node" >/dev/null 2>&1 || true
    pkill -f "payload_manager_node" >/dev/null 2>&1 || true
    pkill -f "mock_inspection_camera_node" >/dev/null 2>&1 || true
    pkill -f "report_manager_node" >/dev/null 2>&1 || true
  }

  sleep "$timeout_sec"
  cp "/tmp/orimus_scenario_launch_${scenario_id}.log" "$log_path" || true
  cleanup_scenario

  if [[ ! -f "$marker_path" ]]; then
    echo "FAIL: scenario $scenario_id expectation completion_marker expected file, observed missing, see log $log_path"
    return 1
  fi
  if [[ ! -f "$report_path" ]]; then
    echo "FAIL: scenario $scenario_id expectation report expected file, observed missing, see log $log_path"
    return 1
  fi

  python3 /workspace/backend/scripts/check_scenario_result.py \
    "$scenario_id" \
    --manifest "$MANIFEST_PATH" \
    --report "$report_path"
}

run_one() {
  local scenario_id="$1"
  local policy_command
  policy_command="$(scenario_field "$scenario_id" "expected.backend_policy_denial.command_type")"
  if [[ -n "$policy_command" ]]; then
    run_backend_policy_scenario "$scenario_id"
  else
    run_ros_scenario "$scenario_id"
  fi
}

run_all() {
  local passed=0
  local failed=0
  local failed_ids=()
  while read -r scenario_id; do
    echo "RUN: $scenario_id"
    if run_one "$scenario_id"; then
      passed=$((passed + 1))
    else
      failed=$((failed + 1))
      failed_ids+=("$scenario_id")
    fi
  done < <(scenario_ids)

  echo "SUMMARY: ${passed} passed, ${failed} failed"
  if [[ "$failed" -gt 0 ]]; then
    echo "FAILED: ${failed_ids[*]}"
    return 1
  fi
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

if [[ "$1" == "--all" ]]; then
  run_all
else
  run_one "$1"
fi
