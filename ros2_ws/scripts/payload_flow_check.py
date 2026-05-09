import sys
import time

import rclpy
from core_interfaces.msg import PayloadCommand, PayloadResult, PerceptionEvent
from rclpy.node import Node


class PayloadFlowCheck(Node):
    def __init__(self) -> None:
        super().__init__("payload_flow_check")
        self.result_received = False
        self.event_received = False
        self.command_pub = self.create_publisher(
            PayloadCommand,
            "payload/command_request",
            10,
        )
        self.result_sub = self.create_subscription(
            PayloadResult,
            "payload/result",
            self.handle_result,
            10,
        )
        self.event_sub = self.create_subscription(
            PerceptionEvent,
            "perception/events",
            self.handle_event,
            10,
        )

    def publish_scan(self) -> None:
        command = PayloadCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = "payload_flow_check_scan"
        command.payload_id = "inspection_camera_001"
        command.payload_type = "mock_inspection_camera"
        command.command_type = "scan"
        command.target_x = 4.0
        command.target_y = 2.0
        command.target_z = 0.0
        command.duration_sec = 1.0
        self.command_pub.publish(command)

    def handle_result(self, msg: PayloadResult) -> None:
        if msg.result_type == "inspection_scan" and msg.success:
            self.result_received = True

    def handle_event(self, msg: PerceptionEvent) -> None:
        if msg.event_type == "person_detected":
            self.event_received = True


def main() -> int:
    rclpy.init()
    node = PayloadFlowCheck()
    try:
        deadline = time.time() + 10.0
        published = False

        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            if not published and node.count_publishers("payload/command") > 0:
                node.publish_scan()
                published = True
            if node.result_received and node.event_received:
                print("PAYLOAD_FLOW_CHECK_OK")
                return 0

        print(
            "PAYLOAD_FLOW_CHECK_FAILED "
            f"published={published} "
            f"result={node.result_received} "
            f"event={node.event_received}",
            file=sys.stderr,
        )
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())

