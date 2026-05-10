from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import rclpy
import yaml
from core_interfaces.msg import MissionState, PayloadCommand, RobotCommand
from rclpy.node import Node


@dataclass(frozen=True)
class MissionStep:
    name: str
    target: str
    command_type: str
    duration_sec: float
    linear_x: float = 0.0
    linear_y: float = 0.0
    yaw_rate: float = 0.0
    max_speed: float = 0.5
    payload_id: str = ""
    payload_type: str = ""
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0


class MissionManagerNode(Node):
    """Run a small demo mission through the ORIMUS safety gate."""

    def __init__(self) -> None:
        super().__init__("mission_manager")

        self.mission_id = self.declare_parameter(
            "mission_id",
            "demo_forward_stop",
        ).value
        self.mission_name = self.declare_parameter(
            "mission_name",
            "Demo Forward Stop",
        ).value
        self.autostart = bool(self.declare_parameter("autostart", True).value)
        self.mission_config_path = str(
            self.declare_parameter("mission_config_path", "").value
        )
        self.completion_marker_path = str(
            self.declare_parameter("completion_marker_path", "").value
        )

        self.command_pub = self.create_publisher(
            RobotCommand,
            "robot/command_request",
            10,
        )
        self.payload_command_pub = self.create_publisher(
            PayloadCommand,
            "payload/command_request",
            10,
        )
        self.state_pub = self.create_publisher(MissionState, "mission/state", 10)

        self.steps = self.load_mission_steps()

        self.current_step_index = -1
        self.current_step_started = self.get_clock().now()
        self.mission_started = False
        self.mission_complete = False

        self.timer = self.create_timer(0.2, self.tick)
        self.publish_state("created", "Mission manager ready")
        self.get_logger().info(
            f"ORIMUS mission manager started with {len(self.steps)} steps"
        )

    def tick(self) -> None:
        if self.mission_complete:
            return

        if not self.mission_started:
            if self.autostart:
                self.start_mission()
            return

        current_step = self.steps[self.current_step_index]
        elapsed = (
            self.get_clock().now() - self.current_step_started
        ).nanoseconds / 1_000_000_000.0

        if elapsed >= current_step.duration_sec:
            self.advance_step()

    def start_mission(self) -> None:
        self.mission_started = True
        self.current_step_index = 0
        self.current_step_started = self.get_clock().now()
        self.publish_state("running", "Mission started")
        self.publish_step(self.steps[self.current_step_index])

    def advance_step(self) -> None:
        self.current_step_index += 1

        if self.current_step_index >= len(self.steps):
            self.mission_complete = True
            self.publish_state("completed", "Mission completed")
            self.write_completion_marker()
            self.get_logger().info("Mission completed")
            return

        self.current_step_started = self.get_clock().now()
        step = self.steps[self.current_step_index]
        self.publish_state("running", f"Running step: {step.name}")
        self.publish_step(step)

    def publish_step(self, step: MissionStep) -> None:
        if step.target == "robot":
            self.publish_robot_step_command(step)
        elif step.target == "payload":
            self.publish_payload_step_command(step)
        else:
            raise ValueError(f"Unsupported mission step target: {step.target}")

    def publish_robot_step_command(self, step: MissionStep) -> None:
        command = RobotCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = f"{self.mission_id}_{step.name}_{command.stamp.sec}"
        command.command_type = step.command_type
        command.linear_x = step.linear_x
        command.linear_y = step.linear_y
        command.yaw_rate = step.yaw_rate
        command.max_speed = step.max_speed
        command.details_json = f'{{"mission_id":"{self.mission_id}","step":"{step.name}"}}'

        self.command_pub.publish(command)
        self.get_logger().info(f"Published robot mission step command: {step.name}")

    def publish_payload_step_command(self, step: MissionStep) -> None:
        command = PayloadCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = f"{self.mission_id}_{step.name}_{command.stamp.sec}"
        command.payload_id = step.payload_id
        command.payload_type = step.payload_type
        command.command_type = step.command_type
        command.target_x = step.target_x
        command.target_y = step.target_y
        command.target_z = step.target_z
        command.duration_sec = step.duration_sec
        command.details_json = f'{{"mission_id":"{self.mission_id}","step":"{step.name}"}}'

        self.payload_command_pub.publish(command)
        self.get_logger().info(f"Published payload mission step command: {step.name}")

    def load_mission_steps(self) -> list[MissionStep]:
        if not self.mission_config_path:
            return self.default_steps()

        config_path = Path(self.mission_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Mission config not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as config_file:
            mission_data = yaml.safe_load(config_file) or {}

        self.mission_id = str(mission_data.get("mission_id", self.mission_id))
        self.mission_name = str(mission_data.get("name", self.mission_name))
        step_data = mission_data.get("steps", [])

        if not isinstance(step_data, list) or not step_data:
            raise ValueError(f"Mission config has no steps: {config_path}")

        steps = [self.parse_step(step) for step in step_data]
        self.get_logger().info(f"Loaded mission config: {config_path}")
        return steps

    @staticmethod
    def parse_step(step_data: dict) -> MissionStep:
        return MissionStep(
            name=str(step_data["name"]),
            target=str(step_data.get("target", "robot")).lower(),
            command_type=str(step_data["command_type"]),
            duration_sec=float(step_data.get("duration_sec", 1.0)),
            linear_x=float(step_data.get("linear_x", 0.0)),
            linear_y=float(step_data.get("linear_y", 0.0)),
            yaw_rate=float(step_data.get("yaw_rate", 0.0)),
            max_speed=float(step_data.get("max_speed", 0.5)),
            payload_id=str(step_data.get("payload_id", "")),
            payload_type=str(step_data.get("payload_type", "")),
            target_x=float(step_data.get("target_x", 0.0)),
            target_y=float(step_data.get("target_y", 0.0)),
            target_z=float(step_data.get("target_z", 0.0)),
        )

    @staticmethod
    def default_steps() -> list[MissionStep]:
        return [
            MissionStep(
                name="stand",
                target="robot",
                command_type="stand",
                duration_sec=1.0,
            ),
            MissionStep(
                name="walk_forward",
                target="robot",
                command_type="walk_velocity",
                duration_sec=3.0,
                linear_x=0.25,
                max_speed=0.5,
            ),
            MissionStep(
                name="stop",
                target="robot",
                command_type="stop",
                duration_sec=1.0,
            ),
            MissionStep(
                name="sit",
                target="robot",
                command_type="sit",
                duration_sec=1.0,
            ),
        ]

    def publish_state(self, state: str, message: str) -> None:
        mission_state = MissionState()
        mission_state.stamp = self.get_clock().now().to_msg()
        mission_state.mission_id = self.mission_id
        mission_state.name = self.mission_name
        mission_state.state = state
        mission_state.current_step = self.current_step_name()
        mission_state.progress = self.progress()
        mission_state.message = message
        self.state_pub.publish(mission_state)

    def current_step_name(self) -> str:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index].name
        return ""

    def progress(self) -> float:
        if self.mission_complete:
            return 1.0
        if self.current_step_index < 0:
            return 0.0
        return float(self.current_step_index) / float(len(self.steps))

    def write_completion_marker(self) -> None:
        if not self.completion_marker_path:
            return

        marker_path = Path(self.completion_marker_path)
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("completed\n", encoding="utf-8")


def main(args: Iterable[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MissionManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
