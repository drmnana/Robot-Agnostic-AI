import threading
from typing import Iterable

import rclpy
import uvicorn
from core_interfaces.msg import (
    MissionCommand,
    MissionEvent,
    MissionState,
    PayloadState,
    PerceptionEvent,
    RobotState,
    SafetyEvent,
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rclpy.node import Node


class CommandResponse(BaseModel):
    status: str
    mission_id: str
    command_type: str


class MissionApiBridgeNode(Node):
    """Expose mission command HTTP endpoints and publish ROS MissionCommand messages."""

    def __init__(self) -> None:
        super().__init__("mission_api_bridge")

        self.host = str(self.declare_parameter("host", "0.0.0.0").value)
        self.port = int(self.declare_parameter("port", 8010).value)
        self.command_pub = self.create_publisher(MissionCommand, "mission/command", 10)
        self.state_lock = threading.Lock()
        self.latest_mission_state: dict | None = None
        self.latest_robot_state: dict | None = None
        self.latest_payload_state: dict | None = None
        self.latest_perception_event: dict | None = None
        self.latest_safety_event: dict | None = None
        self.event_history_limit = int(
            self.declare_parameter("event_history_limit", 50).value
        )
        self.event_history: list[dict] = []

        self.create_subscription(MissionState, "mission/state", self.on_mission_state, 10)
        self.create_subscription(MissionEvent, "mission/events", self.on_mission_event, 10)
        self.create_subscription(RobotState, "robot/state", self.on_robot_state, 10)
        self.create_subscription(PayloadState, "payload/state", self.on_payload_state, 10)
        self.create_subscription(
            PerceptionEvent,
            "perception/events",
            self.on_perception_event,
            10,
        )
        self.create_subscription(SafetyEvent, "safety/events", self.on_safety_event, 10)

        self.app = FastAPI(title="ORIMUS Mission API Bridge", version="0.1.0")
        self.configure_routes()
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        self.get_logger().info(f"Mission API bridge listening on {self.host}:{self.port}")

    def configure_routes(self) -> None:
        @self.app.get("/health")
        def health() -> dict:
            return {"status": "ok", "service": "mission-api-bridge"}

        @self.app.post("/missions/{mission_id}/{command_type}", response_model=CommandResponse)
        def command_mission(mission_id: str, command_type: str) -> CommandResponse:
            normalized_command = command_type.strip().lower()
            if normalized_command not in {"start", "pause", "resume", "cancel", "reset"}:
                raise HTTPException(status_code=400, detail="Unsupported mission command")

            self.publish_mission_command(mission_id, normalized_command)
            return CommandResponse(
                status="accepted",
                mission_id=mission_id,
                command_type=normalized_command,
            )

        @self.app.get("/runtime/state")
        def runtime_state() -> dict:
            return self.get_runtime_snapshot()

        @self.app.get("/runtime/mission")
        def runtime_mission() -> dict:
            return self.get_cached_resource("mission")

        @self.app.get("/runtime/robot")
        def runtime_robot() -> dict:
            return self.get_cached_resource("robot")

        @self.app.get("/runtime/payload")
        def runtime_payload() -> dict:
            return self.get_cached_resource("payload")

        @self.app.get("/runtime/perception")
        def runtime_perception() -> dict:
            return self.get_cached_resource("perception")

        @self.app.get("/runtime/safety")
        def runtime_safety() -> dict:
            return self.get_cached_resource("safety")

        @self.app.get("/runtime/events")
        def runtime_events() -> dict:
            return self.get_cached_resource("events")

    def publish_mission_command(self, mission_id: str, command_type: str) -> None:
        command = MissionCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = f"http_{mission_id}_{command_type}_{command.stamp.sec}"
        command.mission_id = mission_id
        command.command_type = command_type
        command.details_json = '{"source":"mission_api_bridge"}'
        self.command_pub.publish(command)
        self.get_logger().info(f"Published mission command: {mission_id} {command_type}")

    def on_mission_state(self, msg: MissionState) -> None:
        self.update_cached_resource(
            "mission",
            {
                "stamp": time_to_dict(msg.stamp),
                "mission_id": msg.mission_id,
                "name": msg.name,
                "state": msg.state,
                "current_step": msg.current_step,
                "progress": float(msg.progress),
                "message": msg.message,
            },
        )

    def on_mission_event(self, msg: MissionEvent) -> None:
        self.add_event(
            {
                "stamp": time_to_dict(msg.stamp),
                "category": "mission",
                "event_id": msg.event_id,
                "event_type": msg.event_type,
                "mission_id": msg.mission_id,
                "step_name": msg.step_name,
                "target": msg.target,
                "message": msg.message,
                "details_json": msg.details_json,
            },
        )

    def on_robot_state(self, msg: RobotState) -> None:
        self.update_cached_resource(
            "robot",
            {
                "stamp": time_to_dict(msg.stamp),
                "robot_id": msg.robot_id,
                "platform": msg.platform,
                "mode": msg.mode,
                "connected": bool(msg.connected),
                "estop_active": bool(msg.estop_active),
                "battery_percent": float(msg.battery_percent),
                "pose": {
                    "x": float(msg.x),
                    "y": float(msg.y),
                    "yaw": float(msg.yaw),
                },
                "velocity": {
                    "linear_x": float(msg.linear_x),
                    "linear_y": float(msg.linear_y),
                    "yaw_rate": float(msg.yaw_rate),
                },
                "message": msg.message,
            },
        )

    def on_payload_state(self, msg: PayloadState) -> None:
        self.update_cached_resource(
            "payload",
            {
                "stamp": time_to_dict(msg.stamp),
                "payload_id": msg.payload_id,
                "payload_type": msg.payload_type,
                "state": msg.state,
                "active": bool(msg.active),
                "health": float(msg.health),
                "message": msg.message,
            },
        )

    def on_perception_event(self, msg: PerceptionEvent) -> None:
        event = {
            "stamp": time_to_dict(msg.stamp),
            "category": "perception",
            "event_id": msg.event_id,
            "event_type": msg.event_type,
            "source": msg.source,
            "confidence": float(msg.confidence),
            "frame_id": msg.frame_id,
            "position": {
                "x": float(msg.x),
                "y": float(msg.y),
                "z": float(msg.z),
            },
            "evidence_artifact_url": msg.evidence_artifact_url,
            "evidence_hash": msg.evidence_hash,
            "details_json": msg.details_json,
            "message": f"{msg.event_type} from {msg.source}",
        }
        self.update_cached_resource("perception", event)
        self.add_event(event)

    def on_safety_event(self, msg: SafetyEvent) -> None:
        event = {
            "stamp": time_to_dict(msg.stamp),
            "category": "safety",
            "event_id": msg.event_id,
            "severity": msg.severity,
            "source": msg.source,
            "rule": msg.rule,
            "command_id": msg.command_id,
            "command_blocked": bool(msg.command_blocked),
            "message": msg.message,
            "event_type": msg.rule,
        }
        self.update_cached_resource("safety", event)
        self.add_event(event)

    def update_cached_resource(self, resource: str, value: dict) -> None:
        with self.state_lock:
            if resource == "mission":
                self.latest_mission_state = value
            elif resource == "robot":
                self.latest_robot_state = value
            elif resource == "payload":
                self.latest_payload_state = value
            elif resource == "perception":
                self.latest_perception_event = value
            elif resource == "safety":
                self.latest_safety_event = value

    def add_event(self, event: dict) -> None:
        with self.state_lock:
            self.event_history.append(event)
            if len(self.event_history) > self.event_history_limit:
                self.event_history = self.event_history[-self.event_history_limit :]

    def get_runtime_snapshot(self) -> dict:
        with self.state_lock:
            return {
                "bridge": {
                    "connected": True,
                    "service": "mission-api-bridge",
                },
                "mission": self.latest_mission_state,
                "robot": self.latest_robot_state,
                "payload": self.latest_payload_state,
                "perception": self.latest_perception_event,
                "safety": self.latest_safety_event,
                "events": list(self.event_history),
            }

    def get_cached_resource(self, resource: str) -> dict:
        snapshot = self.get_runtime_snapshot()
        if resource not in snapshot:
            raise HTTPException(status_code=404, detail="Unknown runtime resource")

        return {
            "resource": resource,
            "data": snapshot[resource],
        }

    def run_server(self) -> None:
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        server.run()


def time_to_dict(stamp) -> dict:
    return {
        "sec": int(stamp.sec),
        "nanosec": int(stamp.nanosec),
    }


def main(args: Iterable[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MissionApiBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
