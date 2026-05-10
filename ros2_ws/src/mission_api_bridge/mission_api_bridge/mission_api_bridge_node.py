import threading
from typing import Iterable

import rclpy
import uvicorn
from core_interfaces.msg import MissionCommand
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
            if normalized_command not in {"start", "pause", "resume", "cancel"}:
                raise HTTPException(status_code=400, detail="Unsupported mission command")

            self.publish_mission_command(mission_id, normalized_command)
            return CommandResponse(
                status="accepted",
                mission_id=mission_id,
                command_type=normalized_command,
            )

    def publish_mission_command(self, mission_id: str, command_type: str) -> None:
        command = MissionCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = f"http_{mission_id}_{command_type}_{command.stamp.sec}"
        command.mission_id = mission_id
        command.command_type = command_type
        command.details_json = '{"source":"mission_api_bridge"}'
        self.command_pub.publish(command)
        self.get_logger().info(f"Published mission command: {mission_id} {command_type}")

    def run_server(self) -> None:
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        server.run()


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

