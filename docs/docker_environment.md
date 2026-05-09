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

- A base ROS 2 container.
- A simulation container.
- A future Unitree Go2X adapter development container.
- Optional containers for backend, dashboard, and AI services.

## Next Steps

1. Select the ROS 2 distribution.
2. Create a first Dockerfile for ROS 2 development.
3. Add a Docker Compose file for repeatable startup.
4. Add a simple container test command.
5. Document how the user starts and stops the environment.

