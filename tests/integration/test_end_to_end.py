"""Live test: Iceberg table -> backup -> destructive DML -> restore -> parity. Requires AWS account.

Run: ICEBACKUP_DB=<db> pytest -m integration tests/integration
Creates objects only inside ICEBACKUP_DB.ICEBACKUP_IT and drops the (unlocked) backup set at the end.
"""
import os
import uuid

import pytest

from icebackup import restore, verify

pytestmark = pytest.mark.integration
DB = os.environ.get("ICEBACKUP_DB")


@pytest.fixture(scope="module")
def session():
    if not DB:
        pytest.skip("ICEBACKUP_DB not set")
    from snowflake.snowpark import Session
    s = Session.builder.config("connection_name", os.environ.get("SNOWFLAKE_CONNECTION", "default")).create()
    yield s
    s.close()


def test_iceberg_backup_restore_roundtrip(session):
    sch = f"{DB}.ICEBACKUP_IT"
    bs = f"{sch}.IT_BS_{uuid.uuid4().hex[:8].upper()}"
    q = lambda s: session.sql(s).collect()  # noqa: E731
    q(f"CREATE SCHEMA IF NOT EXISTS {sch}")
    q(f"CREATE OR REPLACE ICEBERG TABLE {sch}.T (id INT, v STRING) "
      "CATALOG='SNOWFLAKE' EXTERNAL_VOLUME='SNOWFLAKE_MANAGED'")
    q(f"INSERT INTO {sch}.T SELECT SEQ4(), RANDSTR(10, RANDOM()) FROM TABLE(GENERATOR(ROWCOUNT=>10000))")
    q(f"CREATE OR REPLACE TABLE {sch}.T_GOLDEN AS SELECT * FROM {sch}.T")
    q(f"CREATE BACKUP SET {bs} FOR ICEBERG TABLE {sch}.T")
    try:
        q(f"ALTER BACKUP SET {bs} ADD BACKUP")
        backup_id = q(f'SHOW BACKUPS IN BACKUP SET {bs} ->> SELECT "backup_id" FROM $1')[0][0]
        q(f"DELETE FROM {sch}.T WHERE id % 2 = 0")
        q(restore.restore_sql("ICEBERG TABLE", f"{sch}.T_RESTORED", bs, backup_id))
        result = verify.verify(session, f"{sch}.T_GOLDEN", f"{sch}.T_RESTORED")
        assert result["content_match"] and result["src_rows"] == 10000
    finally:
        q(f"DROP TABLE IF EXISTS {sch}.T_RESTORED")
        for (bid,) in q(f'SHOW BACKUPS IN BACKUP SET {bs} ->> SELECT "backup_id" FROM $1 ORDER BY "created_on"'):
            q(f"ALTER BACKUP SET {bs} DELETE BACKUP IDENTIFIER '{bid}'")
        q(f"DROP BACKUP SET IF EXISTS {bs}")
