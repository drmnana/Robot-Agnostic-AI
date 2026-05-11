from pathlib import Path

import yaml


def is_mission_command_allowed(
    policy_path: Path,
    operator_id: str,
    command_type: str,
) -> bool:
    policy = read_operator_policy(policy_path)
    operator_policy = policy.get("operators", {}).get(operator_id, {})
    allowed_commands = operator_policy.get("allowed_mission_commands", [])
    return command_type in allowed_commands


def read_operator_policy(policy_path: Path) -> dict:
    if not policy_path.exists():
        return {"operators": {}}

    with policy_path.open("r", encoding="utf-8") as file:
        policy = yaml.safe_load(file) or {}

    return policy if isinstance(policy, dict) else {"operators": {}}
