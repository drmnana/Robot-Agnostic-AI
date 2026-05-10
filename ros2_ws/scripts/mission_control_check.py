import sys
import time

import rclpy
from core_interfaces.msg import MissionCommand, MissionState
from rclpy.node import Node


class MissionControlCheck(Node):
    def __init__(self) -> None:
        super().__init__("mission_control_check")
        self.states: list[str] = []
        self.command_pub = self.create_publisher(MissionCommand, "mission/command", 10)
        self.state_sub = self.create_subscription(
            MissionState,
            "mission/state",
            self.handle_state,
            10,
        )

    def handle_state(self, msg: MissionState) -> None:
        self.states.append(msg.state)

    def publish_command(self, command_type: str) -> None:
        command = MissionCommand()
        command.stamp = self.get_clock().now().to_msg()
        command.command_id = f"mission_control_check_{command_type}_{command.stamp.sec}"
        command.mission_id = "control_test"
        command.command_type = command_type
        self.command_pub.publish(command)

    def wait_for_command_subscriber(self, timeout_sec: float = 5.0) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.count_subscribers("mission/command") > 0:
                return True
        return False

    def wait_for_state(self, state: str, timeout_sec: float = 5.0) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if state in self.states:
                return True
        return False


def main() -> int:
    rclpy.init()
    node = MissionControlCheck()
    try:
        if not node.wait_for_command_subscriber():
            print("MISSION_CONTROL_CHECK_FAILED missing command subscriber", file=sys.stderr)
            return 1

        node.publish_command("start")
        if not node.wait_for_state("running"):
            print("MISSION_CONTROL_CHECK_FAILED missing running", file=sys.stderr)
            return 1

        node.publish_command("pause")
        if not node.wait_for_state("paused"):
            print("MISSION_CONTROL_CHECK_FAILED missing paused", file=sys.stderr)
            return 1

        node.publish_command("resume")
        if not node.wait_for_state("running"):
            print("MISSION_CONTROL_CHECK_FAILED missing resumed running", file=sys.stderr)
            return 1

        node.publish_command("cancel")
        if not node.wait_for_state("canceled"):
            print("MISSION_CONTROL_CHECK_FAILED missing canceled", file=sys.stderr)
            return 1

        print("MISSION_CONTROL_CHECK_OK")
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
