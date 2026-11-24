"""Side-by-side restore. Never overwrites the original object (ADR-0001)."""
from __future__ import annotations

import re

KIND_TO_CREATE = {
    "ICEBERG TABLE": "ICEBERG TABLE",
    "DYNAMIC ICEBERG TABLE": "DYNAMIC ICEBERG TABLE",
    "SCHEMA": "SCHEMA",
    "DATABASE": "DATABASE",
}
_UUID = re.compile(r"^[0-9a-fA-F-]{36}$")


def restore_sql(kind: str, target: str, backup_set: str, backup_id: str) -> str:
    if kind not in KIND_TO_CREATE:
        raise ValueError(f"unsupported kind {kind}")
    if not _UUID.match(backup_id):
        raise ValueError("backup_id must be a backup UUID from SHOW BACKUPS IN BACKUP SET")
    # CREATE (not CREATE OR REPLACE): fail if the target exists rather than silently replacing it.
    return f"CREATE {KIND_TO_CREATE[kind]} {target} FROM BACKUP SET {backup_set} IDENTIFIER '{backup_id}'"


def latest_before_sql(backup_set: str, before_ts: str) -> str:
    return (
        f"SHOW BACKUPS IN BACKUP SET {backup_set} ->> "
        f"SELECT \"backup_id\", \"created_on\" FROM $1 "
        f"WHERE \"created_on\" < '{before_ts}'::TIMESTAMP_LTZ ORDER BY \"created_on\" DESC LIMIT 1"
    )
