import json
from pathlib import Path
from typing import Iterable

import rclpy
from core_interfaces.msg import (
    MissionEvent,
    MissionState,
    PayloadResult,
    PayloadState,
    PerceptionEvent,
    RobotState,
    SafetyEvent,
)
from rclpy.node import Node


class ReportManagerNode(Node):
    """Collect mission activity and write a JSON report."""

    def __init__(self) -> None:
        super().__init__("report_manager")

        self.report_path = str(
            self.declare_parameter(
                "report_path",
                "/workspace/reports/latest_mission_report.json",
            ).value
        )

        self.mission_states: list[dict] = []
        self.mission_events: list[dict] = []
        self.safety_events: list[dict] = []
        self.payload_results: list[dict] = []
        self.perception_events: list[dict] = []
        self.latest_robot_state: dict | None = None
        self.latest_payload_states: dict[str, dict] = {}
        self.report_written = False
        self.report_timer = None

        self.create_subscription(MissionState, "mission/state", self.on_mission_state, 10)
        self.create_subscription(MissionEvent, "mission/events", self.on_mission_event, 10)
        self.create_subscription(RobotState, "robot/state", self.on_robot_state, 10)
        self.create_subscription(PayloadState, "payload/state", self.on_payload_state, 10)
        self.create_subscription(PayloadResult, "payload/result", self.on_payload_result, 10)
        self.create_subscription(
            PerceptionEvent,
            "perception/events",
            self.on_perception_event,
            10,
        )
        self.create_subscription(SafetyEvent, "safety/events", self.on_safety_event, 10)

        self.get_logger().info(f"ORIMUS report manager writing to {self.report_path}")

    def on_mission_state(self, msg: MissionState) -> None:
        state = {
            "stamp": self.stamp_to_dict(msg.stamp),
            "mission_id": msg.mission_id,
            "name": msg.name,
            "state": msg.state,
            "current_step": msg.current_step,
            "progress": msg.progress,
            "message": msg.message,
        }
        self.mission_states.append(state)

        if msg.state == "completed" and not self.report_written and self.report_timer is None:
            self.report_timer = self.create_timer(0.5, self.write_report_once)

    def on_mission_event(self, msg: MissionEvent) -> None:
        self.mission_events.append(
            {
                "stamp": self.stamp_to_dict(msg.stamp),
                "event_id": msg.event_id,
                "mission_id": msg.mission_id,
                "event_type": msg.event_type,
                "step_name": msg.step_name,
                "target": msg.target,
                "message": msg.message,
                "details_json": msg.details_json,
            }
        )

    def on_robot_state(self, msg: RobotState) -> None:
        self.latest_robot_state = {
            "stamp": self.stamp_to_dict(msg.stamp),
            "robot_id": msg.robot_id,
            "platform": msg.platform,
            "mode": msg.mode,
            "connected": msg.connected,
            "estop_active": msg.estop_active,
            "battery_percent": msg.battery_percent,
            "x": msg.x,
            "y": msg.y,
            "yaw": msg.yaw,
            "message": msg.message,
        }

    def on_payload_state(self, msg: PayloadState) -> None:
        self.latest_payload_states[msg.payload_id] = {
            "stamp": self.stamp_to_dict(msg.stamp),
            "payload_id": msg.payload_id,
            "payload_type": msg.payload_type,
            "state": msg.state,
            "active": msg.active,
            "health": msg.health,
            "message": msg.message,
        }

    def on_payload_result(self, msg: PayloadResult) -> None:
        self.payload_results.append(
            {
                "stamp": self.stamp_to_dict(msg.stamp),
                "result_id": msg.result_id,
                "payload_id": msg.payload_id,
                "payload_type": msg.payload_type,
                "result_type": msg.result_type,
                "success": msg.success,
                "confidence": msg.confidence,
                "summary": msg.summary,
                "details_json": msg.details_json,
            }
        )

    def on_perception_event(self, msg: PerceptionEvent) -> None:
        self.perception_events.append(
            {
                "stamp": self.stamp_to_dict(msg.stamp),
                "event_id": msg.event_id,
                "event_type": msg.event_type,
                "source": msg.source,
                "confidence": msg.confidence,
                "frame_id": msg.frame_id,
                "x": msg.x,
                "y": msg.y,
                "z": msg.z,
                "details_json": msg.details_json,
            }
        )

    def on_safety_event(self, msg: SafetyEvent) -> None:
        self.safety_events.append(
            {
                "stamp": self.stamp_to_dict(msg.stamp),
                "event_id": msg.event_id,
                "severity": msg.severity,
                "source": msg.source,
                "rule": msg.rule,
                "command_blocked": msg.command_blocked,
                "message": msg.message,
            }
        )

    def write_report(self) -> None:
        report = {
            "report_type": "orimus_mission_report",
            "mission": self.mission_states[-1] if self.mission_states else None,
            "mission_states": self.mission_states,
            "mission_events": self.mission_events,
            "latest_robot_state": self.latest_robot_state,
            "latest_payload_states": list(self.latest_payload_states.values()),
            "payload_results": self.payload_results,
            "perception_events": self.perception_events,
            "safety_events": self.safety_events,
        }

        report_path = Path(self.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.report_written = True
        self.get_logger().info(f"Wrote mission report: {report_path}")

    def write_report_once(self) -> None:
        if self.report_timer is not None:
            self.report_timer.cancel()
            self.destroy_timer(self.report_timer)
            self.report_timer = None

        if not self.report_written:
            self.write_report()

    @staticmethod
    def stamp_to_dict(stamp) -> dict:
        return {"sec": stamp.sec, "nanosec": stamp.nanosec}


def main(args: Iterable[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ReportManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
