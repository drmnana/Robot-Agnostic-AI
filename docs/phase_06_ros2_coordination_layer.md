# Phase 06 - ROS 2 Coordination Layer

## Goal

Build the ROS 2 layer that coordinates robot commands, sensor streams, navigation, transforms, diagnostics, and payload control.

## Why This Phase Matters

ROS 2 is the robotics backbone. It allows many independent nodes to communicate in a structured way.

## Main Tasks

- Create ROS 2 workspace.
- Define ROS 2 packages.
- Add custom messages, services, and actions.
- Create robot manager node.
- Create payload manager node.
- Create safety manager node.
- Create mission bridge node.
- Add diagnostics.
- Add rosbag2 recording strategy.

## Recommended ROS 2 Packages

- core_interfaces
- robot_manager
- payload_manager
- safety_manager
- mission_bridge
- perception_manager
- navigation_manager

## Outputs

- ROS 2 workspace
- Custom ROS 2 interfaces
- Core manager nodes
- Backend-to-ROS bridge
- Basic diagnostics

## Completion Criteria

This phase is complete when the backend can send a structured command into ROS 2 and receive robot or mock robot state back.

