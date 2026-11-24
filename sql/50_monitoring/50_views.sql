-- ACCOUNT_USAGE latency applies (minutes to ~3h). Columns verified against SNOWFLAKE.ACCOUNT_USAGE.
CREATE OR REPLACE VIEW ${ADMIN_DB}.MONITORING.V_BACKUP_INVENTORY AS
SELECT s.catalog_name || '.' || s.schema_name || '.' || s.name AS backup_set,
       s.object_kind,
       COALESCE(s.object_catalog_name || '.', '') || COALESCE(s.object_schema_name || '.', '') || s.object_name AS subject,
       s.backup_policy_name, p.schedule, p.expire_after_days, p.has_retention_lock, s.owner,
       COUNT(b.id)                                   AS live_backups,
       COUNT_IF(b.is_under_legal_hold)               AS legal_holds,
       MAX(b.created)                                AS last_backup_at
FROM SNOWFLAKE.ACCOUNT_USAGE.BACKUP_SETS s
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.BACKUP_POLICIES p ON p.id = s.backup_policy_id AND p.deleted IS NULL
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.BACKUPS b         ON b.backup_set_id = s.id AND b.deleted IS NULL
WHERE s.deleted IS NULL
GROUP BY ALL;

CREATE OR REPLACE VIEW ${ADMIN_DB}.MONITORING.V_BACKUP_FRESHNESS AS
SELECT backup_set, subject, schedule, last_backup_at,
       DATEDIFF('minute', last_backup_at, CURRENT_TIMESTAMP()) AS minutes_since_last_backup
FROM ${ADMIN_DB}.MONITORING.V_BACKUP_INVENTORY
WHERE schedule IS NOT NULL;

CREATE OR REPLACE VIEW ${ADMIN_DB}.MONITORING.V_BACKUP_OPERATIONS_DAILY AS
SELECT DATE_TRUNC('day', h.start_time) AS day, s.name AS backup_set, h.operation_type,
       COUNT(*) AS operations,
       AVG(DATEDIFF('second', h.start_time, h.end_time)) AS avg_seconds,
       MAX(DATEDIFF('second', h.start_time, h.end_time)) AS max_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.BACKUP_OPERATION_HISTORY h
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.BACKUP_SETS s ON s.id = h.backup_set_id
GROUP BY ALL;

CREATE OR REPLACE VIEW ${ADMIN_DB}.MONITORING.V_BACKUP_STORAGE AS
SELECT s.name AS backup_set, s.object_kind, s.object_name,
       SUM(u.incremental_bytes_from_previous_backup) / POWER(1024, 3) AS incremental_gb,
       MAX(u.logical_bytes) / POWER(1024, 3)                          AS max_logical_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.BACKUP_STORAGE_USAGE u
JOIN SNOWFLAKE.ACCOUNT_USAGE.BACKUP_SETS s ON s.id = u.backup_set_id
GROUP BY ALL;

-- Iceberg tables NOT eligible for backup (silently skipped by schema/db sets).
CREATE OR REPLACE VIEW ${ADMIN_DB}.MONITORING.V_ICEBERG_COVERAGE_GAPS AS
SELECT t.table_catalog, t.table_schema, t.table_name, t.is_dynamic, t.is_transient,
       CASE WHEN t.is_transient = 'YES' THEN 'TRANSIENT_NOT_SUPPORTED'
            WHEN s.id IS NULL           THEN 'NO_BACKUP_SET'
            ELSE 'COVERED' END AS status
FROM SNOWFLAKE.ACCOUNT_USAGE.TABLES t
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.BACKUP_SETS s
  ON s.deleted IS NULL AND (
       (s.object_kind = 'DATABASE' AND s.object_name = t.table_catalog)
    OR (s.object_kind = 'SCHEMA'   AND s.object_catalog_name = t.table_catalog AND s.object_name = t.table_schema)
    OR (s.object_kind ILIKE '%TABLE' AND s.object_id = t.table_id))
WHERE t.deleted IS NULL AND t.is_iceberg = 'YES'
QUALIFY ROW_NUMBER() OVER (PARTITION BY t.table_id ORDER BY s.id NULLS LAST) = 1;
-- Note: external-catalog / customer-managed-volume Iceberg tables also appear as COVERED by schema
-- sets but are skipped. `icebackup coverage` resolves this via SHOW ICEBERG TABLES (external_volume_name, catalog_name).
