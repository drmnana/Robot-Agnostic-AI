import json
import math
from typing import Iterable

import rclpy
from core_interfaces.msg import RobotCommand, SafetyEvent
from rclpy.node import Node


class SafetyManagerNode(Node):
    """Validate requested robot commands before forwarding them to the robot."""

    def __init__(self) -> None:
        super().__init__("safety_manager")

        self.max_linear_speed = float(
            self.declare_parameter("max_linear_speed", 0.5).value
        )
        self.max_yaw_rate = float(self.declare_parameter("max_yaw_rate", 1.0).value)
        self.allowed_commands = set(
            self.declare_parameter(
                "allowed_commands",
                [
                    "walk_velocity",
                    "stop",
                    "stand",
                    "sit",
                    "emergency_stop",
                    "clear_estop",
                ],
            ).value
        )

        self.estop_active = False

        self.command_pub = self.create_publisher(RobotCommand, "robot/command", 10)
        self.safety_pub = self.create_publisher(SafetyEvent, "safety/events", 10)
        self.command_request_sub = self.create_subscription(
            RobotCommand,
            "robot/command_request",
            self.handle_command_request,
            10,
        )

        self.get_logger().info("ORIMUS safety manager started")

    def handle_command_request(self, msg: RobotCommand) -> None:
        command = msg.command_type.strip().lower()
        operator_id = self.operator_from_details(msg.details_json)

        if command not in self.allowed_commands:
            self.publish_safety_event(
                severity="warning",
                rule="unknown_command",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Blocked unknown command '{command}'",
            )
            return

        if self.estop_active and command != "clear_estop":
            self.publish_safety_event(
                severity="critical",
                rule="estop_active",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Blocked command '{command}' while emergency stop is active",
            )
            return

        if command == "emergency_stop":
            self.estop_active = True
            forwarded = self.copy_command(msg)
            forwarded.command_type = command
            self.command_pub.publish(forwarded)
            self.publish_safety_event(
                severity="critical",
                rule="manual_estop",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message="Emergency stop forwarded and safety gate locked",
            )
            return

        if command == "clear_estop":
            self.estop_active = False
            forwarded = self.copy_command(msg)
            forwarded.command_type = command
            self.command_pub.publish(forwarded)
            self.publish_safety_event(
                severity="info",
                rule="estop_cleared",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message="Emergency stop cleared",
            )
            return

        forwarded = self.copy_command(msg)
        forwarded.command_type = command

        if command == "walk_velocity":
            self.enforce_velocity_limits(forwarded, operator_id)

        self.command_pub.publish(forwarded)

    def enforce_velocity_limits(self, command: RobotCommand, operator_id: str) -> None:
        requested_speed = math.hypot(command.linear_x, command.linear_y)
        limit = self.resolve_speed_limit(command.max_speed)

        if requested_speed > limit:
            scale = limit / requested_speed
            command.linear_x *= scale
            command.linear_y *= scale
            self.publish_safety_event(
                severity="info",
                rule="max_linear_speed",
                command_id=command.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message=f"Scaled linear speed to {limit:.2f} m/s",
            )

        if abs(command.yaw_rate) > self.max_yaw_rate:
            command.yaw_rate = self.clamp(
                command.yaw_rate,
                -self.max_yaw_rate,
                self.max_yaw_rate,
            )
            self.publish_safety_event(
                severity="info",
                rule="max_yaw_rate",
                command_id=command.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message=f"Clamped yaw rate to {self.max_yaw_rate:.2f} rad/s",
            )

        command.max_speed = limit

    def resolve_speed_limit(self, requested_limit: float) -> float:
        if requested_limit <= 0.0:
            return self.max_linear_speed
        return min(requested_limit, self.max_linear_speed)

    def publish_safety_event(
        self,
        severity: str,
        rule: str,
        command_id: str,
        operator_id: str,
        command_blocked: bool,
        message: str,
    ) -> None:
        stamp = self.get_clock().now().to_msg()
        event = SafetyEvent()
        event.stamp = stamp
        event.event_id = f"{rule}_{stamp.sec}_{stamp.nanosec}"
        event.severity = severity
        event.source = "safety_manager"
        event.rule = rule
        event.command_id = command_id
        event.operator_id = operator_id
        event.command_blocked = command_blocked
        event.message = message
        self.safety_pub.publish(event)
        self.get_logger().warn(message)

    @staticmethod
    def copy_command(command: RobotCommand) -> RobotCommand:
        copied = RobotCommand()
        copied.stamp = command.stamp
        copied.command_id = command.command_id
        copied.command_type = command.command_type
        copied.linear_x = command.linear_x
        copied.linear_y = command.linear_y
        copied.yaw_rate = command.yaw_rate
        copied.target_frame = command.target_frame
        copied.target_x = command.target_x
        copied.target_y = command.target_y
        copied.target_yaw = command.target_yaw
        copied.max_speed = command.max_speed
        copied.details_json = command.details_json
        return copied

    @staticmethod
    def clamp(value: float, lower: float, upper: float) -> float:
        return min(max(value, lower), upper)

    @staticmethod
    def operator_from_details(details_json: str) -> str:
        try:
            details = json.loads(details_json)
        except (TypeError, json.JSONDecodeError):
            return "anonymous"
        operator_id = str(details.get("operator_id", "")).strip()
        return operator_id if operator_id else "anonymous"


def main(args: Iterable[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SafetyManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
