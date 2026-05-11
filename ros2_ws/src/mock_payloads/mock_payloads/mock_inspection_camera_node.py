import hashlib
import json
from pathlib import Path
from typing import Iterable

import rclpy
from core_interfaces.msg import PayloadCommand, PayloadResult, PayloadState, PerceptionEvent
from rclpy.node import Node


class MockInspectionCameraNode(Node):
    """Mock inspection camera that emits deterministic scan results."""

    def __init__(self) -> None:
        super().__init__("mock_inspection_camera")

        self.payload_id = self.declare_parameter(
            "payload_id",
            "inspection_camera_001",
        ).value
        self.payload_type = "mock_inspection_camera"
        self.artifact_root = Path(
            str(
                self.declare_parameter(
                    "artifact_root",
                    "/workspace/data/artifacts",
                ).value
            )
        )
        self.active = False
        self.state = "idle"
        self.health = 1.0
        self.message = "Mock inspection camera ready"

        self.state_pub = self.create_publisher(PayloadState, "payload/state", 10)
        self.result_pub = self.create_publisher(PayloadResult, "payload/result", 10)
        self.perception_pub = self.create_publisher(
            PerceptionEvent,
            "perception/events",
            10,
        )
        self.command_sub = self.create_subscription(
            PayloadCommand,
            "payload/command",
            self.handle_command,
            10,
        )

        self.timer = self.create_timer(1.0, self.publish_state)
        self.get_logger().info("Mock inspection camera started")

    def handle_command(self, msg: PayloadCommand) -> None:
        if msg.payload_type != self.payload_type:
            return

        command = msg.command_type.strip().lower()

        if command == "initialize":
            self.active = False
            self.state = "initialized"
            self.message = "Inspection camera initialized"
        elif command == "start":
            self.active = True
            self.state = "active"
            self.message = "Inspection camera active"
        elif command == "stop":
            self.active = False
            self.state = "idle"
            self.message = "Inspection camera stopped"
        elif command == "calibrate":
            self.state = "calibrated"
            self.message = "Inspection camera calibrated"
        elif command == "scan":
            self.run_scan(msg)
        else:
            self.message = f"Ignored unsupported command: {command}"

        self.publish_state()

    def run_scan(self, msg: PayloadCommand) -> None:
        self.active = True
        self.state = "scanning"
        self.message = "Inspection scan complete"

        result = PayloadResult()
        result.stamp = self.get_clock().now().to_msg()
        result.result_id = f"{self.payload_id}_scan_{result.stamp.sec}"
        artifact = self.write_stub_artifact(result.result_id)
        result.payload_id = self.payload_id
        result.payload_type = self.payload_type
        result.result_type = "inspection_scan"
        result.success = True
        result.confidence = 0.87
        result.summary = "Mock scan detected a person-like target"
        result.details_json = json.dumps(
            {
                "source": "mock",
                "artifact_id": artifact["artifact_id"],
                "artifact_type": artifact["artifact_type"],
            },
            sort_keys=True,
        )
        self.result_pub.publish(result)

        event = PerceptionEvent()
        event.stamp = result.stamp
        event.event_id = f"{self.payload_id}_person_{result.stamp.sec}"
        event.event_type = "person_detected"
        event.source = self.payload_id
        event.confidence = 0.87
        event.frame_id = "map"
        event.x = msg.target_x
        event.y = msg.target_y
        event.z = msg.target_z
        event.evidence_artifact_url = f"/artifacts/{artifact['artifact_id']}/download"
        event.evidence_hash = artifact["sha256_hash"]
        event.details_json = result.details_json
        self.perception_pub.publish(event)

        self.get_logger().info("Published mock inspection scan result")

    def write_stub_artifact(self, result_id: str) -> dict:
        artifact_id = f"{result_id}_artifact"
        artifact_type = "mock-payload-stub"
        artifact_path = self.artifact_root / f"{artifact_id}.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        content = ("mock-payload-stub\n" * 64).encode("utf-8")
        artifact_path.write_bytes(content[:1024].ljust(1024, b" "))
        sha256_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        return {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "file_path": str(artifact_path),
            "sha256_hash": sha256_hash,
        }

    def publish_state(self) -> None:
        state = PayloadState()
        state.stamp = self.get_clock().now().to_msg()
        state.payload_id = self.payload_id
        state.payload_type = self.payload_type
        state.state = self.state
        state.active = self.active
        state.health = self.health
        state.message = self.message
        self.state_pub.publish(state)


def main(args: Iterable[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MockInspectionCameraNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
