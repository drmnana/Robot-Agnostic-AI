#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 launch orimus_bringup mock_go2x.launch.py \
  mission_autostart:=false \
  mission_config_path:=/workspace/configs/missions/control_test.yaml \
  report_path:=/tmp/orimus_control_report.json \
  >/tmp/orimus_mission_control_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 4
python3 scripts/mission_control_check.py

grep -q "Mission paused" /tmp/orimus_mission_control_launch.log
grep -q "Mission resumed" /tmp/orimus_mission_control_launch.log
grep -q "Mission canceled" /tmp/orimus_mission_control_launch.log

echo "MISSION_CONTROL_SMOKE_TEST_OK"

