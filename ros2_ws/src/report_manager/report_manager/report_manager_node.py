import json
import hashlib
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable

import rclpy
from core_interfaces.msg import (
    MissionEvent,
    MissionState,
    PayloadResult,
    PayloadState,
    PerceptionEvent,
    RobotCommand,
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
        self.database_path = str(
            self.declare_parameter(
                "database_path",
                "/workspace/data/orimus.db",
            ).value
        )

        self.report_run_id = ""
        self.mission_states: list[dict] = []
        self.mission_events: list[dict] = []
        self.robot_commands: list[dict] = []
        self.safety_events: list[dict] = []
        self.payload_results: list[dict] = []
        self.perception_events: list[dict] = []
        self.latest_robot_state: dict | None = None
        self.latest_payload_states: dict[str, dict] = {}
        self.report_written = False
        self.report_timer = None

        self.initialize_database()

        self.create_subscription(MissionState, "mission/state", self.on_mission_state, 10)
        self.create_subscription(MissionEvent, "mission/events", self.on_mission_event, 10)
        self.create_subscription(
            RobotCommand,
            "robot/command_request",
            lambda msg: self.on_robot_command(msg, "robot/command_request"),
            10,
        )
        self.create_subscription(
            RobotCommand,
            "robot/command",
            lambda msg: self.on_robot_command(msg, "robot/command"),
            10,
        )
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

        self.get_logger().info(
            f"ORIMUS report manager writing to {self.report_path} and {self.database_path}"
        )

    def on_mission_state(self, msg: MissionState) -> None:
        if msg.state == "running" and msg.message == "Mission started":
            self.start_new_report_run()

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

        if (
            msg.state in {"completed", "canceled", "failed"}
            and not self.report_written
            and self.report_timer is None
        ):
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

    def on_robot_command(self, msg: RobotCommand, topic: str) -> None:
        self.robot_commands.append(
            {
                "stamp": self.stamp_to_dict(msg.stamp),
                "command_id": msg.command_id,
                "topic": topic,
                "command_type": msg.command_type,
                "linear_x": msg.linear_x,
                "linear_y": msg.linear_y,
                "yaw_rate": msg.yaw_rate,
                "max_speed": msg.max_speed,
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
        report_id = self.report_run_id or self.build_report_run_id()
        mission = self.mission_states[-1] if self.mission_states else None
        report = {
            "report_type": "orimus_mission_report",
            "report_id": report_id,
            "mission": mission,
            "mission_states": self.mission_states,
            "mission_events": self.mission_events,
            "robot_commands": self.robot_commands,
            "latest_robot_state": self.latest_robot_state,
            "latest_payload_states": list(self.latest_payload_states.values()),
            "payload_results": self.payload_results,
            "perception_events": self.perception_events,
            "safety_events": self.safety_events,
        }
        content_hash = self.hash_report(report)
        report["content_hash"] = content_hash

        report_path = Path(self.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.persist_report(report, content_hash)
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

    def start_new_report_run(self) -> None:
        if self.mission_states and not self.report_written:
            return

        self.report_run_id = self.build_report_run_id()
        self.mission_states = []
        self.mission_events = []
        self.robot_commands = []
        self.safety_events = []
        self.payload_results = []
        self.perception_events = []
        self.latest_robot_state = None
        self.latest_payload_states = {}
        self.report_written = False

    def build_report_run_id(self) -> str:
        return f"orimus-{uuid.uuid4().hex}"

    @staticmethod
    def hash_report(report: dict) -> str:
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def initialize_database(self) -> None:
        database_path = Path(self.database_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database_path) as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    sector TEXT,
                    outcome TEXT NOT NULL,
                    started_at_sec INTEGER,
                    started_at_nanosec INTEGER,
                    ended_at_sec INTEGER,
                    ended_at_nanosec INTEGER,
                    content_hash TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    mission_event_count INTEGER NOT NULL,
                    robot_command_count INTEGER NOT NULL,
                    safety_event_count INTEGER NOT NULL,
                    perception_event_count INTEGER NOT NULL,
                    payload_result_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    stamp_sec INTEGER,
                    stamp_nanosec INTEGER,
                    category TEXT NOT NULL,
                    event_id TEXT,
                    event_type TEXT,
                    step_name TEXT,
                    target TEXT,
                    message TEXT,
                    details_json TEXT,
                    FOREIGN KEY(report_id) REFERENCES missions(id)
                );

                CREATE TABLE IF NOT EXISTS robot_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    stamp_sec INTEGER,
                    stamp_nanosec INTEGER,
                    command_id TEXT,
                    topic TEXT,
                    command_type TEXT,
                    linear_x REAL,
                    linear_y REAL,
                    yaw_rate REAL,
                    max_speed REAL,
                    details_json TEXT,
                    FOREIGN KEY(report_id) REFERENCES missions(id)
                );

                CREATE TABLE IF NOT EXISTS safety_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    stamp_sec INTEGER,
                    stamp_nanosec INTEGER,
                    event_id TEXT,
                    severity TEXT,
                    source TEXT,
                    rule TEXT,
                    command_blocked INTEGER,
                    message TEXT,
                    FOREIGN KEY(report_id) REFERENCES missions(id)
                );

                CREATE TABLE IF NOT EXISTS perception_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    stamp_sec INTEGER,
                    stamp_nanosec INTEGER,
                    event_id TEXT,
                    event_type TEXT,
                    source TEXT,
                    confidence REAL,
                    frame_id TEXT,
                    x REAL,
                    y REAL,
                    z REAL,
                    details_json TEXT,
                    FOREIGN KEY(report_id) REFERENCES missions(id)
                );

                CREATE TABLE IF NOT EXISTS payload_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    stamp_sec INTEGER,
                    stamp_nanosec INTEGER,
                    result_id TEXT,
                    payload_id TEXT,
                    payload_type TEXT,
                    result_type TEXT,
                    success INTEGER,
                    confidence REAL,
                    summary TEXT,
                    details_json TEXT,
                    FOREIGN KEY(report_id) REFERENCES missions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_missions_ended_at
                    ON missions(ended_at_sec DESC, ended_at_nanosec DESC);
                CREATE INDEX IF NOT EXISTS idx_missions_outcome ON missions(outcome);
                CREATE INDEX IF NOT EXISTS idx_missions_sector ON missions(sector);
                CREATE INDEX IF NOT EXISTS idx_events_report_id ON events(report_id);
                CREATE INDEX IF NOT EXISTS idx_robot_commands_report_id ON robot_commands(report_id);
                CREATE INDEX IF NOT EXISTS idx_safety_events_report_id ON safety_events(report_id);
                CREATE INDEX IF NOT EXISTS idx_perception_events_report_id ON perception_events(report_id);
                CREATE INDEX IF NOT EXISTS idx_payload_results_report_id ON payload_results(report_id);
                """
            )

    def persist_report(self, report: dict, content_hash: str) -> None:
        mission = report.get("mission") or {}
        mission_states = report.get("mission_states", [])
        started = mission_states[0]["stamp"] if mission_states else {}
        ended = mission.get("stamp", {})
        report_id = report["report_id"]

        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                """
                INSERT OR REPLACE INTO missions (
                    id, mission_id, name, sector, outcome,
                    started_at_sec, started_at_nanosec, ended_at_sec, ended_at_nanosec,
                    content_hash, report_json, mission_event_count, robot_command_count,
                    safety_event_count, perception_event_count, payload_result_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    mission.get("mission_id", ""),
                    mission.get("name", ""),
                    self.extract_sector(report),
                    mission.get("state", "unknown"),
                    started.get("sec"),
                    started.get("nanosec"),
                    ended.get("sec"),
                    ended.get("nanosec"),
                    content_hash,
                    json.dumps(report, sort_keys=True),
                    len(report.get("mission_events", [])),
                    len(report.get("robot_commands", [])),
                    len(report.get("safety_events", [])),
                    len(report.get("perception_events", [])),
                    len(report.get("payload_results", [])),
                ),
            )
            self.persist_events(connection, report_id, report)
            self.persist_robot_commands(connection, report_id, report)
            self.persist_safety_events(connection, report_id, report)
            self.persist_perception_events(connection, report_id, report)
            self.persist_payload_results(connection, report_id, report)

    @staticmethod
    def extract_sector(report: dict) -> str | None:
        for event in report.get("mission_events", []):
            details = ReportManagerNode.parse_json_object(event.get("details_json", ""))
            sector = details.get("sector")
            if sector:
                return str(sector)
        return None

    @staticmethod
    def parse_json_object(value: str) -> dict:
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def persist_events(connection, report_id: str, report: dict) -> None:
        for event in report.get("mission_events", []):
            stamp = event.get("stamp", {})
            connection.execute(
                """
                INSERT INTO events (
                    report_id, stamp_sec, stamp_nanosec, category, event_id,
                    event_type, step_name, target, message, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    stamp.get("sec"),
                    stamp.get("nanosec"),
                    "mission",
                    event.get("event_id"),
                    event.get("event_type"),
                    event.get("step_name"),
                    event.get("target"),
                    event.get("message"),
                    event.get("details_json"),
                ),
            )

    @staticmethod
    def persist_robot_commands(connection, report_id: str, report: dict) -> None:
        for command in report.get("robot_commands", []):
            stamp = command.get("stamp", {})
            connection.execute(
                """
                INSERT INTO robot_commands (
                    report_id, stamp_sec, stamp_nanosec, command_id, topic,
                    command_type, linear_x, linear_y, yaw_rate, max_speed, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    stamp.get("sec"),
                    stamp.get("nanosec"),
                    command.get("command_id"),
                    command.get("topic"),
                    command.get("command_type"),
                    command.get("linear_x"),
                    command.get("linear_y"),
                    command.get("yaw_rate"),
                    command.get("max_speed"),
                    command.get("details_json"),
                ),
            )

    @staticmethod
    def persist_safety_events(connection, report_id: str, report: dict) -> None:
        for event in report.get("safety_events", []):
            stamp = event.get("stamp", {})
            connection.execute(
                """
                INSERT INTO safety_events (
                    report_id, stamp_sec, stamp_nanosec, event_id, severity,
                    source, rule, command_blocked, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    stamp.get("sec"),
                    stamp.get("nanosec"),
                    event.get("event_id"),
                    event.get("severity"),
                    event.get("source"),
                    event.get("rule"),
                    int(bool(event.get("command_blocked"))),
                    event.get("message"),
                ),
            )

    @staticmethod
    def persist_perception_events(connection, report_id: str, report: dict) -> None:
        for event in report.get("perception_events", []):
            stamp = event.get("stamp", {})
            connection.execute(
                """
                INSERT INTO perception_events (
                    report_id, stamp_sec, stamp_nanosec, event_id, event_type,
                    source, confidence, frame_id, x, y, z, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    stamp.get("sec"),
                    stamp.get("nanosec"),
                    event.get("event_id"),
                    event.get("event_type"),
                    event.get("source"),
                    event.get("confidence"),
                    event.get("frame_id"),
                    event.get("x"),
                    event.get("y"),
                    event.get("z"),
                    event.get("details_json"),
                ),
            )

    @staticmethod
    def persist_payload_results(connection, report_id: str, report: dict) -> None:
        for result in report.get("payload_results", []):
            stamp = result.get("stamp", {})
            connection.execute(
                """
                INSERT INTO payload_results (
                    report_id, stamp_sec, stamp_nanosec, result_id, payload_id,
                    payload_type, result_type, success, confidence, summary, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    stamp.get("sec"),
                    stamp.get("nanosec"),
                    result.get("result_id"),
                    result.get("payload_id"),
                    result.get("payload_type"),
                    result.get("result_type"),
                    int(bool(result.get("success"))),
                    result.get("confidence"),
                    result.get("summary"),
                    result.get("details_json"),
                ),
            )


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
