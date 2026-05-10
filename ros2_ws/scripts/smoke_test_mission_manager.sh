#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

rm -f /tmp/orimus_mission_completed

ros2 launch orimus_bringup mock_go2x.launch.py \
  mission_autostart:=true \
  mission_config_path:=/workspace/configs/missions/demo_forward_stop.yaml \
  completion_marker_path:=/tmp/orimus_mission_completed \
  >/tmp/orimus_mission_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 12

test -f /tmp/orimus_mission_completed
grep -q "completed" /tmp/orimus_mission_completed
grep -q "Mission completed" /tmp/orimus_mission_launch.log
grep -q "Published mission step command: stand" /tmp/orimus_mission_launch.log
grep -q "Published mission step command: walk_forward" /tmp/orimus_mission_launch.log
grep -q "Published mission step command: stop" /tmp/orimus_mission_launch.log
grep -q "Published mission step command: sit" /tmp/orimus_mission_launch.log

echo "MISSION_MANAGER_SMOKE_TEST_OK"
