#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 run mock_go2x_driver mock_go2x_node >/tmp/mock_go2x.log 2>&1 &
NODE_PID=$!

cleanup() {
  kill "$NODE_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2

ros2 topic echo /robot/state --once >/tmp/mock_go2x_state_before.yaml

ros2 topic pub --once /robot/command core_interfaces/msg/RobotCommand \
  "{command_type: 'walk_velocity', linear_x: 0.25, linear_y: 0.0, yaw_rate: 0.1, max_speed: 0.5}" \
  >/tmp/mock_go2x_command.log

sleep 1

ros2 topic echo /robot/state --once >/tmp/mock_go2x_state_after.yaml

grep -q "mode: walking" /tmp/mock_go2x_state_after.yaml
grep -q "linear_x: 0.25" /tmp/mock_go2x_state_after.yaml

echo "MOCK_GO2X_SMOKE_TEST_OK"
