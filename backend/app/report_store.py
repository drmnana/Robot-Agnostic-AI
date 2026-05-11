import json
import sqlite3
from pathlib import Path


def list_reports(database_path: Path) -> list[dict]:
    if not database_path.exists():
        return []

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                mission_id,
                name,
                sector,
                outcome,
                started_at_sec,
                started_at_nanosec,
                ended_at_sec,
                ended_at_nanosec,
                content_hash,
                mission_event_count,
                robot_command_count,
                safety_event_count,
                perception_event_count,
                payload_result_count
            FROM missions
            ORDER BY ended_at_sec DESC, ended_at_nanosec DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_report(database_path: Path, report_id: str) -> dict | None:
    if not database_path.exists():
        return None

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT report_json
            FROM missions
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["report_json"])
