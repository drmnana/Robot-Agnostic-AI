# Docker Environment

## Purpose

This document tracks the Docker-based development setup for the project.

The project will use Windows as the host operating system and Docker as the controlled development environment for ROS 2, simulation, and future robot SDK tooling.

## Current Status

- Git for Windows is installed.
- WSL2 is installed on the user's Windows account.
- Ubuntu is installed and running on the user's Windows account.
- Docker Desktop is installed.
- Docker CLI is available to Codex after restart.
- Docker successfully ran the `hello-world` container.

## Current Notes

Codex can run Docker commands with elevated permission in this environment.

The Codex terminal still does not see the Ubuntu WSL distribution directly, even though the user's own PowerShell reports Ubuntu running under WSL2. Docker itself is working, so this is not blocking the next project step.

## Recommended Docker Strategy

Use Docker Desktop on Windows with the WSL2 backend.

The project should define one or more development containers:

- A base ROS 2 Humble container.
- A simulation container.
- A future Unitree Go2X adapter development container.
- Optional containers for backend, dashboard, and AI services.

## First ROS 2 Distribution

The first ROS 2 distribution selected for this project is ROS 2 Humble.

Reason:

- Humble is a stable long-term support ROS 2 distribution.
- It runs on Ubuntu 22.04.
- Unitree's official ROS 2 materials document Foxy/Humble-oriented setup paths using Cyclone DDS.
- Starting with Humble is more conservative than starting with a newer distribution.

## First Container

The first development container is defined by:

- `docker/ros2-humble/Dockerfile`
- `docker-compose.yml`

Start it from the repository root:

```powershell
docker compose run --rm ros2-dev
```

Inside the container, check ROS 2:

```bash
ros2 --help
echo $RMW_IMPLEMENTATION
```

## Next Steps

1. Build the ROS 2 Humble development image.
2. Verify ROS 2 commands inside the container.
3. Add a minimal ROS 2 workspace.
4. Add mock robot and simulation package scaffolding.
5. Add bringup launch files for repeatable runtime startup.
