# Phase 08 - Payload And Sensor Framework

## Goal

Create a modular system for attaching and controlling sensors or mission payloads.

## Why This Comes After Core Robot Control

Payloads are useful only when the robot can be commanded safely and the software has stable interfaces.

## Main Tasks

- Define payload adapter interface.
- Add payload manager.
- Add payload configuration files.
- Support payload discovery.
- Add calibration flow.
- Add payload health monitoring.
- Add first real or mock payload.

## Candidate Payloads

- RGB camera
- Thermal camera
- Chemical detector
- Laser spectrometer
- Vibration sensor
- Microphone
- LiDAR

## Common Payload Interface

- initialize
- start
- stop
- calibrate
- get status
- stream data
- run measurement
- return result

## Outputs

- Payload adapter specification
- Payload manager
- First payload adapter
- Payload configuration files

## Completion Criteria

This phase is complete when a payload can be registered, started, monitored, and used by a mission.

