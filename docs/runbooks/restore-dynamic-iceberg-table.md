# Runbook: restore a dynamic Iceberg table

- Prefer restoring the **schema** set: base tables + DT come back together. But the DT keeps its original
  query text. Verified: a schema-restored DT whose query used `ICEBERG_BACKUP_LAB.CORE.ORDERS_ICE` kept
  reading the **original** `CORE.ORDERS_ICE`, not `CORE_RESTORED.ORDERS_ICE`.
- **Fix (verified):** check every restored DT with
  `SHOW DYNAMIC TABLES IN SCHEMA <db>.<restored_schema> ->> SELECT "name","text" FROM $1;`
  and recreate any that reference the original schema, pointing at the restored inputs:
  ```sql
  CREATE OR REPLACE DYNAMIC ICEBERG TABLE ICEBERG_BACKUP_LAB.CORE_RESTORED.ORDERS_DAILY_DIT
    TARGET_LAG = '1 hour' WAREHOUSE = BACKUP_OPS_WH
    CATALOG = 'SNOWFLAKE' EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    AS SELECT DATE_TRUNC('day', order_ts)::DATE AS order_day, COUNT(*) AS orders, SUM(amount) AS revenue
       FROM ICEBERG_BACKUP_LAB.CORE_RESTORED.ORDERS_ICE GROUP BY 1;
  ```
  Result: DT ACTIVE, SUM(orders) = 1,000,000 = restored base rows, revenue matches. The recreated DT is a
  new object with a full initial refresh; it does not carry the backup's DT state.
- Table set: `CREATE DYNAMIC ICEBERG TABLE <name>_RESTORED FROM BACKUP SET <SET> IDENTIFIER '<id>';`
- Restored DTs come back **suspended** and re-initialize on first refresh (full refresh cost on the DT
  warehouse). Budget for it before resuming: `ALTER DYNAMIC TABLE <t> RESUME;`
- Usually a DT does not need restoring at all — fix the base table and let it refresh. Restore the DT
  only when you need its historical state.
