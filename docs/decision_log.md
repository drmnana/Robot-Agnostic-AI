# Decision Log

This document records important project decisions so they are not lost in chat history.

## Decisions

### 000 - Project Name Is ORIMUS

Status: Accepted

Decision:
The system name is ORIMUS.

Reason:
ORIMUS gives the project a clear identity while the engineering architecture remains robot-agnostic and modular.

### 001 - Use A Modular Robot-Agnostic Architecture

Status: Accepted

Decision:
The system should be designed as a robot-agnostic autonomy platform with robot-specific adapters.

Reason:
This allows the same mission, AI, perception, safety, and dashboard layers to support different robot platforms.

### 002 - Keep Project Documents In The Repository

Status: Accepted

Decision:
Architecture, roadmap, phase plans, and important decisions should be saved as files inside the project folder.

Reason:
This keeps the project recoverable and prevents important details from existing only in chat memory.

### 003 - Use Phased Development

Status: Accepted

Decision:
The project will be developed in phases, starting with foundation, environment setup, interfaces, simulation, backend, ROS 2 coordination, then hardware integration.

Reason:
This reduces complexity and avoids debugging too many unstable parts at the same time.

### 004 - First Robot Platform Is Unitree Go2X

Status: Accepted

Decision:
The first robot platform target will be the Unitree Go2X.

Reason:
Starting with one specific robot keeps early development focused. Additional robot platforms can be added later through the platform adapter structure.

### 005 - Start With Simulation

Status: Accepted

Decision:
The first development target will be simulation rather than immediate real-hardware control.

Reason:
Simulation allows mission logic, safety rules, interfaces, and dashboard concepts to be tested before risking real robot hardware.

### 006 - Prefer Windows-Friendly Development

Status: Accepted

Decision:
The development workflow should be friendly to Windows because that is the user's preferred environment.

Reason:
A comfortable development environment is important for learning and steady progress. ROS 2 compatibility details may still require WSL2 Ubuntu, Docker, or a hybrid setup.

### 007 - Use Docker-Based Development

Status: Accepted

Decision:
The project should use a Docker-based development environment while keeping Windows as the host operating system.

Reason:
Docker provides a more repeatable and higher-quality environment for ROS 2, simulation tools, dependencies, and future deployment. It may be harder to learn at first, but it should reduce long-term setup problems.

### 008 - Start With ROS 2 Humble

Status: Accepted

Decision:
The first ROS 2 development container will use ROS 2 Humble on Ubuntu 22.04.

Reason:
Humble is stable, widely supported, and a conservative match for Unitree Go2X-oriented ROS 2 development with Cyclone DDS.

### 009 - Move Vertically Before Horizontally

Status: Accepted

Decision:
ORIMUS should first build a complete vertical slice around the Unitree Go2X simulation path before adding adapters for other robot platforms.

Reason:
A full working path from command request to safety validation to mock robot behavior gives the project a testable foundation. Additional platforms can be added later through the adapter pattern.

### 010 - First Mission Is A Simple Demo Sequence

Status: Accepted

Decision:
The first mission manager implementation will run a simple demo mission: stand, walk forward, stop, and sit.

Reason:
This gives ORIMUS a complete testable mission path without introducing navigation, mapping, payloads, or dashboard complexity too early.

### 011 - Build Generic Payload Framework Before Specialized Payloads

Status: Accepted

Decision:
ORIMUS should first implement a generic payload command and result framework with a mock inspection camera before adding specialized payloads such as chemical detectors, vibration sensors, or face recognition cameras.

Reason:
A generic payload flow keeps the architecture modular and prevents the first payload from forcing hardware-specific assumptions into the core system.

### 012 - Use YAML Mission Configuration

Status: Accepted

Decision:
Mission definitions should be loaded from YAML configuration files instead of being hardcoded in the mission manager.

Reason:
YAML mission files make it easier to define patrol, inspection, scan, and payload-triggering missions without editing Python code.

### 013 - Mission Steps Can Target Robot Or Payload

Status: Accepted

Decision:
Mission YAML steps can target either the robot command path or the payload command path.

Reason:
Real ORIMUS missions will combine movement and sensor actions, such as walking to a point and triggering an inspection camera, chemical scan, or vibration reading.

## Pending Decisions

- First mission scenario.
- First payload or sensor.
- GitHub repository name.
- Docker runtime strategy on Windows, likely Docker Desktop with WSL2 backend.
