#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
source install/setup.bash

ros2 launch orimus_bringup mock_go2x.launch.py >/tmp/orimus_payload_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 4

ros2 node list >/tmp/orimus_payload_nodes.txt
grep -q "/payload_manager" /tmp/orimus_payload_nodes.txt
grep -q "/mock_inspection_camera" /tmp/orimus_payload_nodes.txt

python3 scripts/payload_flow_check.py

echo "PAYLOAD_MANAGER_SMOKE_TEST_OK"
