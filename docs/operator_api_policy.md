# Operator API Policy

## Purpose

The operator API policy controls which development-mode operator IDs may call mission command API endpoints.

This is operator-to-API authorization. It does not replace, augment, or coordinate with the robot's `safety_manager` or any hardware-level safety constraints. Those are independent layers.

The policy answers:

```text
Is this operator allowed to call this API command?
```

It does not answer:

```text
Is this robot action safe to execute?
```

Robot execution safety remains the responsibility of ROS safety nodes, hardware constraints, emergency stop systems, and future deployment safety controls.

## Config

The development policy lives at:

```text
configs/operator_policy.yaml
```

Example structure:

```yaml
version: 1
operators:
  anonymous:
    allowed_mission_commands:
      - pause
  operator-demo:
    allowed_mission_commands:
      - start
      - pause
      - resume
      - reset
  supervisor-demo:
    allowed_mission_commands:
      - start
      - pause
      - resume
      - cancel
      - reset
```

## Behavior

- Missing or blank `X-ORIMUS-Operator` is treated as `anonymous`.
- Allowed commands are forwarded to the ROS mission API bridge.
- Denied commands return HTTP `403`.
- Denied commands are logged by the backend.
- Persistent denied-command audit is deferred until ORIMUS decides whether denied API calls belong in the mission SQLite audit trail or a separate backend audit log.

## Development-Mode Limitation

This policy uses self-asserted operator IDs. It is not production authentication or non-repudiable identity.

Production deployment requires real authentication and authorization such as JWT, mTLS, SSO, hardware-backed identity, or another approved identity system.
