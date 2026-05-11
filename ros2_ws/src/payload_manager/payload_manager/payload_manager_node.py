import json
from typing import Iterable

import rclpy
from core_interfaces.msg import PayloadCommand, PayloadState, SafetyEvent
from rclpy.node import Node


class PayloadManagerNode(Node):
    """Validate payload requests before forwarding them to payload adapters."""

    def __init__(self) -> None:
        super().__init__("payload_manager")

        self.allowed_payload_types = set(
            self.declare_parameter(
                "allowed_payload_types",
                ["mock_inspection_camera", "mock_environment_sensor"],
            ).value
        )
        self.allowed_commands = set(
            self.declare_parameter(
                "allowed_commands",
                ["initialize", "start", "stop", "scan", "calibrate"],
            ).value
        )
        self.max_duration_sec = float(
            self.declare_parameter("max_duration_sec", 10.0).value
        )

        self.command_pub = self.create_publisher(PayloadCommand, "payload/command", 10)
        self.state_pub = self.create_publisher(PayloadState, "payload/manager_state", 10)
        self.safety_pub = self.create_publisher(SafetyEvent, "safety/events", 10)
        self.request_sub = self.create_subscription(
            PayloadCommand,
            "payload/command_request",
            self.handle_payload_request,
            10,
        )

        self.publish_manager_state("ready", "Payload manager ready")
        self.get_logger().info("ORIMUS payload manager started")

    def handle_payload_request(self, msg: PayloadCommand) -> None:
        payload_type = msg.payload_type.strip().lower()
        command_type = msg.command_type.strip().lower()
        operator_id = self.operator_from_details(msg.details_json)

        if payload_type not in self.allowed_payload_types:
            self.publish_safety_event(
                severity="warning",
                rule="unknown_payload_type",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Blocked payload type '{payload_type}'",
            )
            return

        if command_type not in self.allowed_commands:
            self.publish_safety_event(
                severity="warning",
                rule="unknown_payload_command",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Blocked payload command '{command_type}'",
            )
            return

        forwarded = self.copy_command(msg)
        forwarded.payload_type = payload_type
        forwarded.command_type = command_type

        if forwarded.duration_sec > self.max_duration_sec:
            forwarded.duration_sec = self.max_duration_sec
            self.publish_safety_event(
                severity="info",
                rule="payload_duration_limit",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message=f"Clamped payload duration to {self.max_duration_sec:.1f}s",
            )

        self.command_pub.publish(forwarded)
        self.publish_manager_state("forwarded", f"Forwarded payload command {command_type}")

    def publish_manager_state(self, state: str, message: str) -> None:
        payload_state = PayloadState()
        payload_state.stamp = self.get_clock().now().to_msg()
        payload_state.payload_id = "payload_manager"
        payload_state.payload_type = "manager"
        payload_state.state = state
        payload_state.active = True
        payload_state.health = 1.0
        payload_state.message = message
        self.state_pub.publish(payload_state)

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
        event.source = "payload_manager"
        event.rule = rule
        event.command_id = command_id
        event.operator_id = operator_id
        event.command_blocked = command_blocked
        event.message = message
        self.safety_pub.publish(event)
        self.get_logger().warn(message)

    @staticmethod
    def copy_command(command: PayloadCommand) -> PayloadCommand:
        copied = PayloadCommand()
        copied.stamp = command.stamp
        copied.command_id = command.command_id
        copied.payload_id = command.payload_id
        copied.payload_type = command.payload_type
        copied.command_type = command.command_type
        copied.target_x = command.target_x
        copied.target_y = command.target_y
        copied.target_z = command.target_z
        copied.duration_sec = command.duration_sec
        copied.details_json = command.details_json
        return copied

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
    node = PayloadManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
