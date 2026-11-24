"""Row-count and content-hash parity between a source and a restored table."""
from __future__ import annotations


def parity_sql(source: str, restored: str) -> str:
    return (
        f"SELECT (SELECT COUNT(*) FROM {source}) AS src_rows, (SELECT COUNT(*) FROM {restored}) AS rst_rows, "
        f"(SELECT HASH_AGG(*) FROM {source}) = (SELECT HASH_AGG(*) FROM {restored}) AS content_match"
    )


def verify(session, source: str, restored: str) -> dict:
    row = session.sql(parity_sql(source, restored)).collect()[0]
    return {"src_rows": row[0], "rst_rows": row[1], "content_match": bool(row[2])}
