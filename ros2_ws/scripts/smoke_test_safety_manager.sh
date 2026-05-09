#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 run mock_go2x_driver mock_go2x_node >/tmp/mock_go2x.log 2>&1 &
MOCK_PID=$!
ros2 run safety_manager safety_manager_node >/tmp/safety_manager.log 2>&1 &
SAFETY_PID=$!

cleanup() {
  kill "$MOCK_PID" "$SAFETY_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2

ros2 topic pub --once /robot/command_request core_interfaces/msg/RobotCommand \
  "{command_type: 'walk_velocity', linear_x: 2.0, linear_y: 0.0, yaw_rate: 2.0, max_speed: 2.0}" \
  >/tmp/safety_command.log

sleep 1
ros2 topic echo /robot/state --once >/tmp/safety_state.yaml
grep -q "mode: walking" /tmp/safety_state.yaml
grep -q "linear_x: 0.5" /tmp/safety_state.yaml
grep -q "yaw_rate: 1.0" /tmp/safety_state.yaml

ros2 topic pub --once /robot/command_request core_interfaces/msg/RobotCommand \
  "{command_type: 'emergency_stop'}" \
  >/tmp/safety_estop.log

sleep 1
ros2 topic pub --once /robot/command_request core_interfaces/msg/RobotCommand \
  "{command_type: 'walk_velocity', linear_x: 0.1, linear_y: 0.0, yaw_rate: 0.0, max_speed: 0.5}" \
  >/tmp/safety_blocked.log

sleep 1
grep -q "Emergency stop forwarded and safety gate locked" /tmp/safety_manager.log
grep -q "Blocked command 'walk_velocity' while emergency stop is active" /tmp/safety_manager.log

echo "SAFETY_MANAGER_SMOKE_TEST_OK"
