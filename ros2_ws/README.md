# ROS 2 Workspace

This workspace contains the ROS 2 packages for the robot-agnostic AI system.

## Packages

- `core_interfaces`: shared messages for robot commands, robot state, payload state, missions, perception events, and safety events.
- `mock_go2x_driver`: simulation-first mock driver for the Unitree Go2X platform.

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
