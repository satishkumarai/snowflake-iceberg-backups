# Runbook: scheduled backup missing / failed

Note: ACCOUNT_USAGE lags; use `<db>.INFORMATION_SCHEMA.BACKUPS` for real-time checks during an incident.

Alert: `V_BACKUP_FRESHNESS.minutes_since_last_backup > 2 * schedule`.

Common causes:
1. **Owner privileges lost** — set owner needs SELECT/USAGE on the subject, any privilege on its parent
   schema+DB, and on the set's own schema+DB. Fix grants to the owner role.
2. **Unsupported policy on a table** (aggregation, projection, storage lifecycle) — backup creation fails
   for the whole schema/db set. Remove policy or move the table.
3. **Subject object was replaced** (`CREATE OR REPLACE`) — set is orphaned. Create a new set (prefer schema
   scope, ADR-0001); keep the old one until its backups expire.
4. **Policy suspended** — `SHOW BACKUP SETS` and `ALTER BACKUP SET <s> RESUME BACKUP POLICY;`
