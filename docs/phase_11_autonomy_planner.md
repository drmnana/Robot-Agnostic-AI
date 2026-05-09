# Phase 11 - Autonomy Planner

## Goal

Add higher-level autonomous decision-making.

## Why This Comes Later

Autonomy depends on mission management, robot control, perception, payloads, and safety. It should be added after those foundations exist.

## Main Tasks

- Define autonomy levels.
- Add behavior tree execution.
- Add structured AI planning.
- Add task decomposition.
- Add operator approval checkpoints.
- Add safety validation before execution.
- Add failure recovery behaviors.

## Important Rule

The AI planner should generate structured plans, not direct motor commands.

Recommended flow:

```text
AI planner -> structured plan -> mission manager -> safety manager -> robot or payload action
```

## Example Autonomy Behaviors

- Patrol route
- Inspect target
- Follow person, where allowed
- Return to base
- Replan around blocked path
- Stop and request operator approval
- Trigger payload scan

## Outputs

- Autonomy planner
- Behavior tree definitions
- AI command schema
- Safety validation workflow
- Recovery behavior library

## Completion Criteria

This phase is complete when the system can perform a controlled multi-step mission with limited autonomous decision-making and safety checks.

