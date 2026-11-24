"""Find Iceberg tables that backups will not protect, beyond what ACCOUNT_USAGE shows."""
from __future__ import annotations


def classify(row: dict) -> str:
    """row: one SHOW ICEBERG TABLES record (lower-cased keys)."""
    if str(row.get("catalog_name", "")).upper() not in ("", "SNOWFLAKE"):
        return "EXTERNAL_CATALOG_NOT_SUPPORTED"
    if str(row.get("external_volume_name", "")).upper() not in ("", "SNOWFLAKE_MANAGED"):
        return "CUSTOMER_MANAGED_STORAGE_NOT_SUPPORTED"
    if str(row.get("kind", "")).upper() == "TRANSIENT":
        return "TRANSIENT_NOT_SUPPORTED"
    return "ELIGIBLE"


def scan(session, database: str) -> list[dict]:
    # SHOW ICEBERG TABLES has catalog/volume but no transient flag; SHOW TABLES "kind" has it.
    kinds = {
        (r["schema_name"], r["name"]): r["kind"]
        for r in (x.as_dict() for x in session.sql(f"SHOW TABLES IN DATABASE {database}").collect())
    }
    out = []
    for r in session.sql(f"SHOW ICEBERG TABLES IN DATABASE {database}").collect():
        d = {k.lower(): v for k, v in r.as_dict().items()}
        d["kind"] = kinds.get((d["schema_name"], d["name"]), "")
        out.append({"table": f'{d["database_name"]}.{d["schema_name"]}.{d["name"]}', "status": classify(d)})
    return out
