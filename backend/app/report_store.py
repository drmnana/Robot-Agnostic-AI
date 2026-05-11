import json
import sqlite3
from pathlib import Path


def list_reports(
    database_path: Path,
    outcome: str | None = None,
    mission_id: str | None = None,
    sector: str | None = None,
    date_from: int | None = None,
    date_to: int | None = None,
    perception_event_type: str | None = None,
    has_safety_event: bool | None = None,
    command_blocked: bool | None = None,
) -> list[dict]:
    if not database_path.exists():
        return []

    query_filters = []
    params = []

    if outcome:
        query_filters.append("m.outcome = ?")
        params.append(outcome)
    if mission_id:
        query_filters.append("(m.mission_id LIKE ? OR m.name LIKE ?)")
        mission_pattern = f"%{mission_id}%"
        params.extend([mission_pattern, mission_pattern])
    if sector:
        query_filters.append("m.sector = ?")
        params.append(sector)
    if date_from is not None:
        query_filters.append("m.ended_at_sec >= ?")
        params.append(date_from)
    if date_to is not None:
        query_filters.append("m.ended_at_sec <= ?")
        params.append(date_to)
    if perception_event_type:
        query_filters.append(
            """
            EXISTS (
                SELECT 1
                FROM perception_events pe
                WHERE pe.report_id = m.id
                  AND pe.event_type = ?
            )
            """
        )
        params.append(perception_event_type)
    if has_safety_event is True:
        query_filters.append(
            """
            EXISTS (
                SELECT 1
                FROM safety_events se
                WHERE se.report_id = m.id
            )
            """
        )
    elif has_safety_event is False:
        query_filters.append(
            """
            NOT EXISTS (
                SELECT 1
                FROM safety_events se
                WHERE se.report_id = m.id
            )
            """
        )
    if command_blocked is not None:
        query_filters.append(
            """
            EXISTS (
                SELECT 1
                FROM safety_events se
                WHERE se.report_id = m.id
                  AND se.command_blocked = ?
            )
            """
        )
        params.append(1 if command_blocked else 0)

    where_clause = f"WHERE {' AND '.join(query_filters)}" if query_filters else ""

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            SELECT
                m.id,
                m.mission_id,
                m.name,
                m.sector,
                m.outcome,
                m.started_at_sec,
                m.started_at_nanosec,
                m.ended_at_sec,
                m.ended_at_nanosec,
                m.content_hash,
                m.mission_event_count,
                m.robot_command_count,
                m.safety_event_count,
                m.perception_event_count,
                m.payload_result_count
            FROM missions m
            {where_clause}
            ORDER BY m.ended_at_sec DESC, m.ended_at_nanosec DESC
            """,
            params,
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
