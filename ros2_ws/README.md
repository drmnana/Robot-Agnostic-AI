# ROS 2 Workspace

This workspace contains the ROS 2 packages for the robot-agnostic AI system.

## Packages

- `core_interfaces`: shared messages for robot commands, robot state, payload state, missions, perception events, and safety events.
- `mock_go2x_driver`: simulation-first mock driver for the Unitree Go2X platform.
- `safety_manager`: command validation gate that forwards safe robot commands and blocks unsafe requests.
- `mission_manager`: simple mission sequencer that publishes command requests through the safety manager.
- `payload_manager`: payload command validation gate.
- `mock_payloads`: simulation-first mock payload adapters.
- `report_manager`: mission report collector.
- `mission_api_bridge`: ROS-aware HTTP bridge for mission commands.
- `orimus_bringup`: launch files for starting ORIMUS runtime configurations.

## Build Inside Docker

From the repository root:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && colcon build"
```

## Run The Mock Go2X Driver

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && ros2 run mock_go2x_driver mock_go2x_node"
```

The mock node publishes:

- `robot/state`
- `safety/events`

The mock node subscribes to:

- `robot/command`

## Run The Safety Manager Flow

The safety manager receives requested commands on `robot/command_request` and forwards approved commands to `robot/command`.

```text
operator / mission / AI
        |
        v
robot/command_request
        |
        v
safety_manager
        |
        v
robot/command
        |
        v
mock_go2x_driver
```

Smoke test:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && bash scripts/smoke_test_safety_manager.sh"
```

## Launch Mock Go2X Runtime

Start the mock Go2X driver and safety manager together:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && ros2 launch orimus_bringup mock_go2x.launch.py"
```

Launch smoke test:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && bash scripts/smoke_test_mock_launch.sh"
```

## Run The Demo Mission

The demo mission stands, walks forward briefly, stops, and sits.

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && source install/setup.bash && ros2 launch orimus_bringup mock_go2x.launch.py mission_autostart:=true mission_config_path:=/workspace/configs/missions/demo_forward_stop.yaml"
```

Mission smoke test:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && bash scripts/smoke_test_mission_manager.sh"
```

Mission API bridge smoke test:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && bash scripts/smoke_test_mission_api_bridge.sh"
```

## Run The Mock Payload Flow

The mock payload flow is:

```text
payload/command_request -> payload_manager -> payload/command -> mock_inspection_camera
```

Payload smoke test:

```powershell
docker compose run --rm ros2-dev bash -lc "cd ros2_ws && bash scripts/smoke_test_payload_manager.sh"
```
