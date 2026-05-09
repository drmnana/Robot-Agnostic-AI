# Safety Assumptions

## Purpose

This document defines the first safety assumptions for the autonomous AI robot dog system.

These assumptions are intentionally conservative. They should be reviewed before any real robot control, payload activation, or field testing.

## Core Rule

The AI system must never directly control robot motors or hazardous payloads.

Recommended authority chain:

```text
AI planner -> structured command -> mission manager -> safety manager -> robot or payload adapter
```

Manual emergency stop must always have the highest priority.

## Version 1 Safety Boundaries

Version 1 should be simulation-first.

The system should not control a real Unitree Go2X until:

- The command interface is documented.
- The safety manager exists.
- Emergency stop behavior is tested.
- Manual override is tested.
- Basic command limits are enforced.
- Logs are recorded.
- A human operator is present.

## Motion Safety

The system should enforce:

- Maximum speed limits.
- Stop command availability at all times.
- No autonomous movement without mission approval.
- No movement outside approved test zones.
- No movement near people until proximity rules are implemented.
- No stair, road, traffic, or public-area testing in early versions.

## Payload Safety

Payloads should be disabled by default.

Any payload with possible risk, such as laser, chemical sampling, heat, sound, or physical contact, must require:

- Explicit mission authorization.
- Safety validation.
- Operator visibility.
- Clear logs.
- Immediate shutdown path.

## AI Safety

AI outputs must be treated as suggestions or structured plans, not trusted commands.

The system should reject AI output that:

- Skips safety validation.
- Requests direct motor control.
- Requests unsafe speed or distance.
- Requests hazardous payload activation without approval.
- Conflicts with geofence, battery, operator, or emergency-stop rules.

## Communication Loss

If communication is lost, the robot should enter a safe state.

Initial safe behavior:

```text
Stop motion -> disable payload activity -> wait for operator recovery
```

Return-to-base behavior can be added later after navigation and safety validation are mature.

## Logging

The system should log:

- Operator commands.
- AI plans.
- Approved commands.
- Rejected commands.
- Robot telemetry.
- Payload events.
- Safety interventions.
- Emergency stop events.

## Open Safety Questions

- What maximum speed should be allowed in simulation?
- What maximum speed should be allowed on the real robot?
- What minimum distance should the robot keep from people?
- What payloads are allowed in version 1?
- What should happen when battery is low?
- Who is authorized to approve hazardous payload actions?

