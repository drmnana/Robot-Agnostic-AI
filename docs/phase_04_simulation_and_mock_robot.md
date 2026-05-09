# Phase 04 - Simulation And Mock Robot

## Goal

Build a safe test environment before controlling a real robot.

The first development target for this project is simulation.

## Why This Comes Before Real Hardware

Real robots can fall, collide, damage equipment, or behave unexpectedly.

A mock robot and simulation layer let us test mission logic, safety rules, backend communication, and dashboard features without risking hardware.

## Main Tasks

- Create a mock robot adapter.
- Create a Unitree Go2X-oriented simulation path.
- Simulate robot state, battery, pose, and movement.
- Simulate basic sensor data.
- Create simple mission playback.
- Add failure cases such as low battery or communication loss.
- Evaluate simulation tools such as Gazebo, Isaac Sim, or Webots.

## Mock Robot Capabilities

- Stand
- Sit
- Stop
- Walk velocity command
- Navigate to waypoint
- Report battery
- Report pose
- Report health
- Trigger emergency stop

## Outputs

- Mock robot adapter
- Simulation strategy document
- Basic test mission
- Fake telemetry stream
- Fake payload stream

## Initial Implementation

The first mock robot implementation is the `mock_go2x_driver` ROS 2 package.

It provides:

- A mock Unitree Go2X-like node.
- Simulated robot state.
- Basic velocity command handling.
- Stop, stand, sit, emergency stop, and clear emergency stop commands.
- Safety events for blocked or unknown commands.

The command path now routes through the `safety_manager` package:

```text
/robot/command_request -> safety_manager -> /robot/command -> mock_go2x_driver
```

## Completion Criteria

This phase is complete when we can run a simple mission without real hardware and see robot state changes in software.
