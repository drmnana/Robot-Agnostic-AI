# Phase 07 - First Robot Platform Adapter

## Goal

Connect the system to the first real robot platform or official simulator.

The first selected robot platform is Unitree Go2X.

## Why Only One Robot First

Supporting many robots too early will slow the project down.

The correct strategy is to build one platform adapter well, then generalize the pattern for other robots.

## Main Tasks

- Choose first robot platform.
- Study official SDK/API.
- Create platform adapter package.
- Map common commands to vendor commands.
- Read battery, pose, health, and motion state.
- Implement emergency stop.
- Test manual movement.
- Test controlled autonomous command.

## Candidate First Platforms

- Unitree Go2X
- Unitree B2
- Boston Dynamics Spot
- Ghost Robotics platform

## Common Adapter Interface

- stand
- sit
- stop
- emergency stop
- walk velocity
- get battery
- get pose
- get health
- get joint state

## Outputs

- First real platform adapter
- Platform setup document
- Basic movement test
- Safety test checklist

## Completion Criteria

This phase is complete when the system can safely send basic commands to the first robot and receive reliable telemetry.
