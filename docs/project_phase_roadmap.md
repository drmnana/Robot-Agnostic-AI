# Project Phase Roadmap

## Purpose

This roadmap divides the autonomous AI robot dog system into logical implementation phases.

The goal is to build the project in a controlled order so that each phase creates a stable foundation for the next one. This avoids mixing too many difficult problems at the same time.

## Recommended Build Order

For this project, we should not begin with the frontend alone or with real robot control immediately.

The safest order is:

1. Architecture, requirements, and safety boundaries
2. Development environment and repository setup
3. Core interfaces and shared data contracts
4. Simulation and mock robot control
5. Backend mission system
6. ROS 2 coordination layer
7. Robot platform adapter for the first robot
8. Payload and sensor framework
9. Perception and AI models
10. Frontend operator dashboard
11. Autonomy planner and behavior execution
12. Safety hardening, logging, replay, and deployment

The backend, ROS 2 interfaces, simulation, and mock adapters should come before the final frontend because the dashboard needs real system concepts to connect to. However, we can still create a simple frontend prototype earlier for visualization and testing.

## Phase Documents

- [Phase 01 - Project Foundation](phase_01_project_foundation.md)
- [Phase 02 - Development Environment](phase_02_development_environment.md)
- [Phase 03 - Core Interfaces](phase_03_core_interfaces.md)
- [Phase 04 - Simulation And Mock Robot](phase_04_simulation_and_mock_robot.md)
- [Phase 05 - Backend Mission System](phase_05_backend_mission_system.md)
- [Phase 06 - ROS 2 Coordination Layer](phase_06_ros2_coordination_layer.md)
- [Phase 07 - First Robot Platform Adapter](phase_07_first_robot_platform_adapter.md)
- [Phase 08 - Payload And Sensor Framework](phase_08_payload_and_sensor_framework.md)
- [Phase 09 - Perception And AI Models](phase_09_perception_and_ai_models.md)
- [Phase 10 - Operator Dashboard](phase_10_operator_dashboard.md)
- [Phase 11 - Autonomy Planner](phase_11_autonomy_planner.md)
- [Phase 12 - Safety, Logging, Deployment](phase_12_safety_logging_deployment.md)

## Current Priority

The current priority is improving repeatability without committing to CTO-dependent hardware choices.

The simulation-first vertical slice is working. The next safe work should focus on:

- simulated mission scenario library
- mission YAML validation
- scenario test harnesses
- dashboard/operator workflow polish
- backend API documentation
- health checks and CI-ready verification

Real robot platform integration and real payload integration are deferred for CTO review.
