import hashlib
import json
import sqlite3
from pathlib import Path


class ArtifactNotFoundError(Exception):
    pass


class ArtifactHashMismatchError(Exception):
    pass


class ArtifactStore:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self.database_path = database_path
        self.artifact_root = artifact_root

    def list_artifacts(
        self,
        mission_id: str | None = None,
        report_id: str | None = None,
        source: str | None = None,
        artifact_type: str | None = None,
    ) -> list[dict]:
        if not self.database_path.exists():
            return []

        filters = []
        params = []
        if mission_id:
            filters.append("mission_id = ?")
            params.append(mission_id)
        if report_id:
            filters.append("report_id = ?")
            params.append(report_id)
        if source:
            filters.append("source = ?")
            params.append(source)
        if artifact_type:
            filters.append("artifact_type = ?")
            params.append(artifact_type)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""
                SELECT
                    artifact_id,
                    mission_id,
                    report_id,
                    source,
                    artifact_type,
                    file_path,
                    sha256_hash,
                    created_at,
                    metadata_json
                FROM evidence_artifacts
                {where_clause}
                ORDER BY created_at DESC, artifact_id DESC
                """,
                params,
            ).fetchall()

        return [dict(row) for row in rows]

    def get_artifact(self, artifact_id: str) -> dict | None:
        if not self.database_path.exists():
            return None

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT
                    artifact_id,
                    mission_id,
                    report_id,
                    source,
                    artifact_type,
                    file_path,
                    sha256_hash,
                    created_at,
                    metadata_json
                FROM evidence_artifacts
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            ).fetchone()

        return dict(row) if row is not None else None

    def artifact_file(self, artifact_id: str) -> Path:
        artifact = self.get_artifact(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)

        file_path = Path(artifact["file_path"])
        resolved = file_path.resolve()
        root = self.artifact_root.resolve()
        if root not in resolved.parents and resolved != root:
            raise ArtifactNotFoundError(artifact_id)
        if not resolved.exists() or not resolved.is_file():
            raise ArtifactNotFoundError(artifact_id)

        actual_hash = hash_file(resolved)
        if actual_hash != artifact["sha256_hash"]:
            raise ArtifactHashMismatchError(artifact_id)

        return resolved

    def register_artifact(
        self,
        *,
        artifact_id: str,
        mission_id: str,
        report_id: str,
        source: str,
        artifact_type: str,
        file_path: Path,
        created_at: float,
        metadata: dict | None = None,
    ) -> dict:
        self.initialize()
        metadata_json = json.dumps(metadata or {}, sort_keys=True)
        artifact = {
            "artifact_id": artifact_id,
            "mission_id": mission_id,
            "report_id": report_id,
            "source": source,
            "artifact_type": artifact_type,
            "file_path": str(file_path),
            "sha256_hash": hash_file(file_path),
            "created_at": created_at,
            "metadata_json": metadata_json,
        }
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO evidence_artifacts (
                    artifact_id,
                    mission_id,
                    report_id,
                    source,
                    artifact_type,
                    file_path,
                    sha256_hash,
                    created_at,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact["artifact_id"],
                    artifact["mission_id"],
                    artifact["report_id"],
                    artifact["source"],
                    artifact["artifact_type"],
                    artifact["file_path"],
                    artifact["sha256_hash"],
                    artifact["created_at"],
                    artifact["metadata_json"],
                ),
            )
        return artifact

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    metadata_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_mission_id
                    ON evidence_artifacts(mission_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_report_id
                    ON evidence_artifacts(report_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_source
                    ON evidence_artifacts(source);
                CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_type
                    ON evidence_artifacts(artifact_type);
                """
            )


def hash_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
