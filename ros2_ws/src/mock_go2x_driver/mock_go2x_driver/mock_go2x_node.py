import json
import math

import rclpy
from core_interfaces.msg import RobotCommand, RobotState, SafetyEvent
from rclpy.node import Node


class MockGo2XNode(Node):
    """Simulation-first mock driver for a Unitree Go2X-like robot."""

    def __init__(self) -> None:
        super().__init__("mock_go2x_driver")

        self.robot_id = self.declare_parameter("robot_id", "go2x_mock_001").value
        self.platform = self.declare_parameter("platform", "unitree_go2x").value
        self.state_rate_hz = float(self.declare_parameter("state_rate_hz", 10.0).value)

        self.mode = "standing"
        self.connected = True
        self.estop_active = False
        self.battery_percent = 100.0
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.yaw_rate = 0.0
        self.message = "Mock Go2X ready"
        self.last_update_time = self.get_clock().now()

        self.state_pub = self.create_publisher(RobotState, "robot/state", 10)
        self.safety_pub = self.create_publisher(SafetyEvent, "safety/events", 10)
        self.command_sub = self.create_subscription(
            RobotCommand,
            "robot/command",
            self.handle_command,
            10,
        )

        period = 1.0 / self.state_rate_hz
        self.timer = self.create_timer(period, self.update_and_publish_state)
        self.get_logger().info("Mock Go2X driver started")

    def handle_command(self, msg: RobotCommand) -> None:
        command = msg.command_type.strip().lower()
        operator_id = self.operator_from_details(msg.details_json)

        if self.estop_active and command != "clear_estop":
            self.publish_safety_event(
                severity="warning",
                rule="estop_active",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Blocked command '{command}' because emergency stop is active",
            )
            return

        if command == "walk_velocity":
            self.apply_velocity_command(msg)
        elif command == "stop":
            self.stop_motion("Stop command received")
        elif command == "stand":
            self.mode = "standing"
            self.message = "Standing"
        elif command == "sit":
            self.stop_motion("Sitting")
            self.mode = "sitting"
        elif command == "emergency_stop":
            self.stop_motion("Emergency stop active")
            self.estop_active = True
            self.mode = "estop"
            self.publish_safety_event(
                severity="critical",
                rule="manual_estop",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=False,
                message="Emergency stop activated",
            )
        elif command == "clear_estop":
            self.estop_active = False
            self.mode = "standing"
            self.message = "Emergency stop cleared"
        else:
            self.publish_safety_event(
                severity="warning",
                rule="unknown_command",
                command_id=msg.command_id,
                operator_id=operator_id,
                command_blocked=True,
                message=f"Unknown robot command '{command}'",
            )

    def apply_velocity_command(self, msg: RobotCommand) -> None:
        max_speed = msg.max_speed if msg.max_speed > 0.0 else 0.5
        requested_speed = math.hypot(msg.linear_x, msg.linear_y)

        if requested_speed > max_speed:
            scale = max_speed / requested_speed
            self.linear_x = msg.linear_x * scale
            self.linear_y = msg.linear_y * scale
            self.publish_safety_event(
                severity="info",
                rule="max_speed_limit",
                command_id=msg.command_id,
                operator_id=self.operator_from_details(msg.details_json),
                command_blocked=False,
                message="Velocity command scaled to max_speed",
            )
        else:
            self.linear_x = msg.linear_x
            self.linear_y = msg.linear_y

        self.yaw_rate = max(min(msg.yaw_rate, 1.0), -1.0)
        self.mode = "walking"
        self.message = "Walking velocity command active"

    def stop_motion(self, message: str) -> None:
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.yaw_rate = 0.0
        self.message = message

    def update_and_publish_state(self) -> None:
        now = self.get_clock().now()
        dt = (now - self.last_update_time).nanoseconds / 1_000_000_000.0
        self.last_update_time = now

        if self.mode == "walking":
            self.x += (
                math.cos(self.yaw) * self.linear_x - math.sin(self.yaw) * self.linear_y
            ) * dt
            self.y += (
                math.sin(self.yaw) * self.linear_x + math.cos(self.yaw) * self.linear_y
            ) * dt
            self.yaw = self.normalize_angle(self.yaw + self.yaw_rate * dt)
            self.battery_percent = max(0.0, self.battery_percent - 0.002 * dt)

        state = RobotState()
        state.stamp = now.to_msg()
        state.robot_id = self.robot_id
        state.platform = self.platform
        state.mode = self.mode
        state.connected = self.connected
        state.estop_active = self.estop_active
        state.battery_percent = float(self.battery_percent)
        state.x = self.x
        state.y = self.y
        state.yaw = self.yaw
        state.linear_x = self.linear_x
        state.linear_y = self.linear_y
        state.yaw_rate = self.yaw_rate
        state.message = self.message
        self.state_pub.publish(state)

    def publish_safety_event(
        self,
        severity: str,
        rule: str,
        command_id: str,
        operator_id: str,
        command_blocked: bool,
        message: str,
    ) -> None:
        event = SafetyEvent()
        event.stamp = self.get_clock().now().to_msg()
        event.event_id = f"{rule}_{event.stamp.sec}_{event.stamp.nanosec}"
        event.severity = severity
        event.source = "mock_go2x_driver"
        event.rule = rule
        event.command_id = command_id
        event.operator_id = operator_id
        event.command_blocked = command_blocked
        event.message = message
        self.safety_pub.publish(event)
        self.get_logger().warn(message)

    @staticmethod
    def normalize_angle(angle: float) -> float:
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    @staticmethod
    def operator_from_details(details_json: str) -> str:
        try:
            details = json.loads(details_json)
        except (TypeError, json.JSONDecodeError):
            return "anonymous"
        operator_id = str(details.get("operator_id", "")).strip()
        return operator_id if operator_id else "anonymous"


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MockGo2XNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
