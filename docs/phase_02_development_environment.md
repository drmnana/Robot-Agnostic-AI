# Phase 02 - Development Environment

## Goal

Prepare the development environment so the project can be built, tested, and saved properly.

## Why This Comes Early

If the environment is unstable, every later phase becomes harder. ROS 2, Python, simulation tools, Git, and hardware SDKs must be organized carefully.

## Main Tasks

- Install and configure Git.
- Create a GitHub repository.
- Connect the local project folder to GitHub.
- Choose the operating system strategy.
- Choose the ROS 2 distribution.
- Install Python tooling.
- Install development editor tools.
- Decide whether to use Docker.
- Create a repeatable setup guide.

## Important Decisions

- Windows only, Linux only, or Windows plus WSL2?
- ROS 2 Humble, Iron, Jazzy, or another distribution?
- Native install or Docker-based development?
- Simulation locally or on a stronger workstation?

## Recommended Direction

For ROS 2 robotics development, Linux or WSL2 is usually easier than pure Windows.

If the target robot SDK strongly prefers Linux, we should use Ubuntu with ROS 2.

Current preference:

- User prefers Windows as the host operating system.
- Development should use Docker for repeatability and quality.
- Docker Desktop with the WSL2 backend is likely the best Windows-friendly approach.
- Project files should remain accessible from Windows while robot and ROS 2 tooling runs inside containers.

## Outputs

- GitHub repository
- Local Git repository
- Development setup document
- Docker development environment definition
- Basic project folder structure
- Tool installation checklist

## Completion Criteria

This phase is complete when:

- The project is tracked by Git.
- The project is backed up to GitHub.
- The development environment can run basic scripts.
- ROS 2 installation path is decided.
- The setup process is documented.
