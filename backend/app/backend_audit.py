import sqlite3
import time
import uuid
from pathlib import Path


class BackendAuditStore:
    """Append-only backend API audit event store."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.initialize()

    def record_event(
        self,
        event_type: str,
        decision: str,
        operator_id: str,
        request_path: str,
        mission_id: str = "",
        command_type: str = "",
        reason: str = "",
        source_ip: str | None = None,
        retention_class: str = "standard",
    ) -> dict:
        event_id = f"backend-{uuid.uuid4().hex}"
        created_at_sec = time.time()
        event = {
            "id": event_id,
            "created_at_sec": created_at_sec,
            "event_type": event_type,
            "operator_id": operator_id,
            "decision": decision,
            "mission_id": mission_id,
            "command_type": command_type,
            "reason": reason,
            "request_path": request_path,
            "source_ip": source_ip,
            "retention_class": retention_class,
        }

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO backend_audit_events (
                    id, created_at_sec, event_type, operator_id, decision,
                    mission_id, command_type, reason, request_path,
                    source_ip, retention_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["id"],
                    event["created_at_sec"],
                    event["event_type"],
                    event["operator_id"],
                    event["decision"],
                    event["mission_id"],
                    event["command_type"],
                    event["reason"],
                    event["request_path"],
                    event["source_ip"],
                    event["retention_class"],
                ),
            )
        return event

    def list_events(
        self,
        operator_id: str | None = None,
        decision: str | None = None,
        event_type: str | None = None,
        date_from: float | None = None,
        date_to: float | None = None,
    ) -> list[dict]:
        filters = []
        params = []

        if operator_id:
            filters.append("operator_id = ?")
            params.append(operator_id)
        if decision:
            filters.append("decision = ?")
            params.append(decision)
        if event_type:
            filters.append("event_type = ?")
            params.append(event_type)
        if date_from is not None:
            filters.append("created_at_sec >= ?")
            params.append(date_from)
        if date_to is not None:
            filters.append("created_at_sec <= ?")
            params.append(date_to)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""
                SELECT
                    id, created_at_sec, event_type, operator_id, decision,
                    mission_id, command_type, reason, request_path,
                    source_ip, retention_class
                FROM backend_audit_events
                {where_clause}
                ORDER BY created_at_sec DESC
                """,
                params,
            ).fetchall()

        return [dict(row) for row in rows]

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS backend_audit_events (
                    id TEXT PRIMARY KEY,
                    created_at_sec REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    operator_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    mission_id TEXT,
                    command_type TEXT,
                    reason TEXT,
                    request_path TEXT NOT NULL,
                    source_ip TEXT,
                    retention_class TEXT NOT NULL DEFAULT 'standard'
                );

                CREATE INDEX IF NOT EXISTS idx_backend_audit_operator_id
                    ON backend_audit_events(operator_id);
                CREATE INDEX IF NOT EXISTS idx_backend_audit_decision
                    ON backend_audit_events(decision);
                CREATE INDEX IF NOT EXISTS idx_backend_audit_event_type
                    ON backend_audit_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_backend_audit_created_at
                    ON backend_audit_events(created_at_sec DESC);
                """
            )
