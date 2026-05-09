# ORIMUS - Architecture Reference

## 1. Project Objective

The goal of ORIMUS is to develop an autonomous AI-powered system that can guide, monitor, and control quadruped robot platforms running through ROS 2 or vendor APIs.

Target robot platforms may include:

- Unitree Go2
- Unitree B2
- Boston Dynamics Spot
- Ghost Robotics platforms
- Future quadruped platforms with compatible APIs or ROS 2 interfaces

The system should be robot-agnostic. This means the core autonomy, AI, perception, safety, dashboard, and mission logic should remain mostly the same, while each robot platform is connected through a dedicated adapter.

The system should also support mission-specific payloads mounted on the robot, such as:

- RGB cameras
- Thermal cameras
- Person-tracking cameras
- Face recognition modules, where legally and ethically allowed
- Chemical detectors
- Laser-based analysis tools
- Vibration sensors
- Acoustic sensors
- LiDAR
- Environmental sensors
- Future payload modules

The first simulated payload adapter is a mock inspection camera. It exists to prove the generic payload command, state, result, and perception event flow before adding specialized hardware.

## 2. Core Design Principle

The most important design principle is:

> Separate robot control, autonomy, perception, safety, mission logic, and payload hardware into clean interchangeable layers.

This prevents the project from becoming tied to one robot vendor or one sensor type.

Instead of building a Unitree-only or Spot-only system, the project should become a reusable autonomy platform that can connect to different robots and payloads.

## 3. High-Level Architecture

```text
Operator / Mission Control
        |
        v
Mission Management Layer
        |
        v
AI Decision & Autonomy Layer
        |
        v
ROS 2 Coordination Layer
        |
        +-------------------------+
        |                         |
        v                         v
Robot Platform Adapter       Payload Adapter Layer
        |                         |
        v                         v
Unitree / Spot / Ghost       Cameras / Chemical / Vibration /
API / SDK / ROS Driver       Thermal / LiDAR / Audio / Other Sensors
        |
        v
Robot Hardware
```

## 4. Main System Layers

### 4.1 Operator And Mission Control

This is the human-facing layer.

It should eventually include:

- Web dashboard or ground control station
- Live robot status
- Live video feeds
- Map view
- Mission planning interface
- Manual override controls
- Emergency stop
- Sensor readings
- Alerts and detections
- Mission logs
- Remote terminal access when needed

Example operator commands:

- Patrol this perimeter.
- Inspect that vehicle.
- Approach the target area and scan for chemicals.
- Track this person.
- Return to base.
- Stop immediately.

## 4.2 Mission Management Layer

This layer turns a high-level goal into a structured mission.

Example:

```text
Mission: Chemical inspection
Target: Zone B

Steps:
1. Navigate to waypoint B1.
2. Stop at a safe distance.
3. Aim chemical detector at target.
4. Activate laser analysis.
5. Record result.
6. Send alert if hazardous compound is detected.
7. Return to standby point.
```

Responsibilities:

- Mission creation
- Mission state tracking
- Task sequencing
- Failure handling
- Operator approval checkpoints
- Mission pause, resume, and cancel
- Safety constraints
- Mission event logging

This layer should not directly control motors or sensors. It should command lower-level modules through defined interfaces.

## 4.3 AI Decision And Autonomy Layer

This is the reasoning and decision-making layer.

It may handle:

- Task planning
- Situational reasoning
- Object detection
- Person detection
- Face recognition, only when legally and ethically approved
- Behavior selection
- Risk assessment
- Sensor fusion
- Target prioritization
- Natural language command interpretation
- Report generation

Important safety rule:

```text
AI planner -> structured command -> safety validator -> ROS 2 action/service -> robot
```

A language model should not directly control motors.

Example structured command:

```json
{
  "action": "navigate_to",
  "target": "Waypoint_B1",
  "constraints": {
    "max_speed": 0.8,
    "avoid_people": true,
    "stop_distance_m": 2.0
  }
}
```

## 4.4 ROS 2 Coordination Layer

ROS 2 should act as the robotics middleware that coordinates communication between robot control, perception, navigation, sensors, mission logic, and diagnostics.

Recommended ROS 2 components:

- Nav2 for navigation
- slam_toolbox or another mapping system
- robot_localization for sensor fusion
- tf2 for coordinate transforms
- rosbag2 for recording and replay
- Lifecycle nodes for reliability
- Behavior trees for mission execution
- DDS configuration for networking

This layer should coordinate:

- Topics
- Services
- Actions
- Sensor streams
- Robot state
- Payload state
- Diagnostics
- Navigation goals
- Transform frames

## 4.5 Robot Platform Adapter Layer

Each robot platform should have a dedicated adapter.

Example:

```text
robot_adapters/
  unitree_go2_adapter/
  unitree_b2_adapter/
  spot_adapter/
  ghost_adapter/
```

Each adapter should expose a common interface to the rest of the system:

```text
walk_velocity()
stop()
sit()
stand()
navigate_assisted()
get_battery()
get_pose()
get_joint_state()
get_robot_health()
emergency_stop()
```

Internally, each adapter talks to the official robot API, SDK, or ROS 2 driver.

Example:

```text
Common Command: walk_velocity(x=0.5, y=0.0, yaw=0.2)

Unitree Adapter -> Unitree SDK command
Spot Adapter    -> Spot API command
Ghost Adapter   -> Ghost Robotics API command
```

## 4.6 Payload Adapter Layer

Payloads should also be modular.

Example:

```text
payload_adapters/
  rgb_camera/
  thermal_camera/
  face_recognition_camera/
  chemical_detector/
  laser_spectrometer/
  vibration_sensor/
  microphone_array/
  lidar/
```

Each payload should expose a common control interface:

```text
initialize()
start()
stop()
calibrate()
get_status()
stream_data()
run_measurement()
return_result()
```

Example payload kits:

```text
Security Kit:
- RGB camera
- Thermal camera
- Microphone
- Person detector

Chemical Inspection Kit:
- Chemical detector
- Laser spectrometer
- Pan/tilt aiming mount
- RGB targeting camera

Perimeter Detection Kit:
- Vibration sensor
- Acoustic sensor
- Long-range camera
```

## 4.7 Perception Layer

The perception layer processes raw sensor data and converts it into useful events.

Example perception capabilities:

- Person detection
- Face recognition
- Vehicle detection
- Animal detection
- Chemical classification
- Vibration signature classification
- Object tracking
- Terrain detection
- Obstacle detection
- Thermal anomaly detection
- Audio event detection

Example event:

```json
{
  "event_type": "person_detected",
  "confidence": 0.91,
  "location": {
    "frame": "map",
    "x": 12.4,
    "y": 7.8
  },
  "source": "front_camera",
  "timestamp": "2026-05-08T12:00:00Z"
}
```

## 4.8 Safety And Control Layer

The safety layer must sit between AI decisions and real robot execution.

It should enforce:

- Emergency stop
- Speed limits
- Geofencing
- Human proximity limits
- Payload safety rules
- Laser activation rules
- Battery return-to-base threshold
- Fall detection
- Communication loss behavior
- Manual override priority
- Platform-specific motion limits

Recommended authority order:

```text
Manual E-stop > Safety Controller > Mission Logic > AI Planner
```

The AI should never be the highest authority in the system.

## 4.9 Data, Logging, And Replay Layer

The system should record:

- ROS bags
- Mission logs
- Sensor readings
- Video snippets
- Detection events
- Operator commands
- Robot telemetry
- Errors and warnings
- AI decisions
- Safety interventions

This is important for:

- Debugging
- Compliance
- Model improvement
- Incident review
- Simulation replay
- Performance evaluation

## 4.10 Simulation And Testing Layer

Before deploying on real robots, the system should support simulation.

Possible simulation tools:

- Gazebo / Ignition Gazebo
- NVIDIA Isaac Sim
- Webots
- Unitree simulation tools, where available
- Spot simulation or mock SDK layer
- ROS 2 mock adapters

The simulation layer should allow testing of:

- Mission logic without robot hardware
- Payload logic without real sensors
- AI behavior using recorded data
- Navigation in simulated maps
- Failure scenarios
- Communication loss
- Low battery behavior
- Sensor malfunction

## 5. Proposed Repository Structure

```text
robot_ai_system/
  apps/
    operator_dashboard/
    mission_server/

  ros2_ws/
    src/
      core_interfaces/
      mission_manager/
      autonomy_engine/
      safety_manager/
      perception_manager/
      navigation_manager/
      payload_manager/
      robot_manager/

      robot_adapters/
        unitree_go2_adapter/
        unitree_b2_adapter/
        spot_adapter/
        ghost_adapter/

      payload_adapters/
        rgb_camera/
        thermal_camera/
        chemical_detector/
        vibration_sensor/
        laser_spectrometer/

      perception_models/
        person_detection/
        face_recognition/
        chemical_analysis/
        vibration_classification/

      simulation/
        worlds/
        robot_models/
        mock_sensors/

  backend/
    api_gateway/
    database/
    event_logger/
    ai_orchestrator/

  frontend/
    dashboard/
    mission_planner/
    video_viewer/

  configs/
    robots/
      unitree_go2.yaml
      unitree_b2.yaml
      spot.yaml
      ghost.yaml

    payloads/
      security_kit.yaml
      chemical_kit.yaml
      vibration_kit.yaml

    missions/
      patrol.yaml
      inspect_target.yaml
      chemical_scan.yaml

  docs/
    architecture_reference.md
    safety_model.md
    platform_adapter_spec.md
    payload_adapter_spec.md
```

## 6. Initial Development Phases

### Phase 1: Architecture And Simulation

- Define system interfaces
- Define ROS 2 messages, actions, and services
- Build mock robot adapter
- Build mock payload adapter
- Build basic mission manager
- Build operator dashboard prototype
- Run missions in simulation

### Phase 2: First Real Robot Integration

- Choose first platform, likely Unitree Go2 or Spot
- Implement platform adapter
- Connect movement, telemetry, battery, pose, and emergency stop
- Test manual control
- Test simple autonomous navigation

### Phase 3: Sensor Payload Integration

- Add RGB camera
- Add person detection
- Add sensor manager
- Add payload status monitoring
- Record data with rosbag2

### Phase 4: Mission Autonomy

- Add mission planner
- Add behavior trees
- Add structured AI decision layer
- Add safety validation
- Add operator approval checkpoints

### Phase 5: Specialized Payloads

- Chemical detector
- Laser analysis module
- Vibration classification
- Thermal inspection
- Face recognition, only with strong privacy and legal controls

### Phase 6: Multi-Platform Support

- Add Unitree B2 adapter
- Add Spot adapter
- Add Ghost adapter
- Standardize robot capabilities
- Support capability discovery

## 7. Immediate Next Questions

Before building the first technical components, the project should answer:

- Which robot platform will be supported first?
- Will the first version run in simulation, on real hardware, or both?
- Which operating system will be used for development?
- Which ROS 2 distribution will be used?
- What is the first mission scenario?
- What is the first payload to integrate?
- What level of autonomy is required in version 1?
- What safety constraints are mandatory from the beginning?

## 8. Working Method

This document should act as the project reference.

As the project develops, each major component should receive its own dedicated document:

- Safety model
- Platform adapter specification
- Payload adapter specification
- Mission manager design
- AI planner design
- ROS 2 interface definitions
- Dashboard design
- Simulation strategy
- Deployment strategy
