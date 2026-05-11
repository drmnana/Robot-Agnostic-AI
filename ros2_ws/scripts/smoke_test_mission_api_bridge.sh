#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 launch orimus_bringup mock_go2x.launch.py \
  mission_autostart:=false \
  mission_config_path:=/workspace/configs/missions/control_test.yaml \
  mission_api_port:=8010 \
  report_path:=/tmp/orimus_api_bridge_report.json \
  >/tmp/orimus_api_bridge_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" >/dev/null 2>&1 || true
  pkill -f "mission_manager_node" >/dev/null 2>&1 || true
  pkill -f "mission_api_bridge_node" >/dev/null 2>&1 || true
  pkill -f "mock_go2x_node" >/dev/null 2>&1 || true
  pkill -f "safety_manager_node" >/dev/null 2>&1 || true
  pkill -f "payload_manager_node" >/dev/null 2>&1 || true
  pkill -f "mock_inspection_camera_node" >/dev/null 2>&1 || true
  pkill -f "report_manager_node" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in {1..30}; do
  if curl -fsS http://127.0.0.1:8010/health >/tmp/orimus_api_bridge_health.json; then
    break
  fi
  sleep 1
done

grep -q "mission-api-bridge" /tmp/orimus_api_bridge_health.json

curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/start >/tmp/orimus_api_start.json
sleep 1
curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/pause >/tmp/orimus_api_pause.json
sleep 1
curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/resume >/tmp/orimus_api_resume.json
sleep 1
curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/cancel >/tmp/orimus_api_cancel.json
sleep 1
curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/reset >/tmp/orimus_api_reset.json
sleep 1
curl -fsS -X POST http://127.0.0.1:8010/missions/control_test/start >/tmp/orimus_api_restart.json
sleep 1
curl -fsS http://127.0.0.1:8010/runtime/state >/tmp/orimus_api_runtime_state.json
curl -fsS http://127.0.0.1:8010/runtime/mission >/tmp/orimus_api_runtime_mission.json
curl -fsS http://127.0.0.1:8010/runtime/robot >/tmp/orimus_api_runtime_robot.json

grep -q '"command_type":"start"' /tmp/orimus_api_start.json
grep -q '"command_type":"pause"' /tmp/orimus_api_pause.json
grep -q '"command_type":"resume"' /tmp/orimus_api_resume.json
grep -q '"command_type":"cancel"' /tmp/orimus_api_cancel.json
grep -q '"command_type":"reset"' /tmp/orimus_api_reset.json
grep -q '"command_type":"start"' /tmp/orimus_api_restart.json
grep -q '"bridge":{"connected":true' /tmp/orimus_api_runtime_state.json
grep -q '"resource":"mission"' /tmp/orimus_api_runtime_mission.json
grep -q '"resource":"robot"' /tmp/orimus_api_runtime_robot.json

grep -q "Mission paused" /tmp/orimus_api_bridge_launch.log
grep -q "Mission resumed" /tmp/orimus_api_bridge_launch.log
grep -q "Mission canceled" /tmp/orimus_api_bridge_launch.log
grep -q "Mission reset" /tmp/orimus_api_bridge_launch.log

echo "MISSION_API_BRIDGE_SMOKE_TEST_OK"
