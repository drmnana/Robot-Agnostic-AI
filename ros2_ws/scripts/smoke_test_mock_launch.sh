#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 launch orimus_bringup mock_go2x.launch.py >/tmp/orimus_mock_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 4

ros2 node list >/tmp/orimus_nodes.txt
grep -q "/mock_go2x_driver" /tmp/orimus_nodes.txt
grep -q "/safety_manager" /tmp/orimus_nodes.txt

ros2 topic echo /robot/state --once >/tmp/orimus_launch_state.yaml
grep -q "platform: unitree_go2x" /tmp/orimus_launch_state.yaml

ros2 topic pub --once /robot/command_request core_interfaces/msg/RobotCommand \
  "{command_type: 'walk_velocity', linear_x: 0.2, linear_y: 0.0, yaw_rate: 0.1, max_speed: 0.5}" \
  >/tmp/orimus_launch_command.log

sleep 1
ros2 topic echo /robot/state --once >/tmp/orimus_launch_state_after.yaml
grep -q "mode: walking" /tmp/orimus_launch_state_after.yaml

echo "ORIMUS_MOCK_LAUNCH_SMOKE_TEST_OK"

