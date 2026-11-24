# Runbook: restore a Snowflake-managed Iceberg table

**Use when:** bad DML/DDL corrupted `<DB>.<SCH>.<TABLE>`. **Role:** BACKUP_OPERATOR.

1. Pause writers (suspend ingest tasks / pipes / dynamic tables downstream).
2. Pick the backup created just **before** the incident:
   ```sql
   SHOW BACKUPS IN BACKUP SET BACKUP_ADMIN.POLICIES.<SET>
     ->> SELECT "created_on","backup_id","is_under_legal_hold" FROM $1
         WHERE "created_on" < '<incident_ts>'::TIMESTAMP_LTZ ORDER BY "created_on" DESC LIMIT 3;
   ```
3. Restore **side-by-side** (never over the original):
   `icebackup restore --set <SET> --backup-id <id> --target <TABLE>_RESTORED`
   (table set -> `CREATE ICEBERG TABLE ... FROM BACKUP SET`; schema set -> `CREATE SCHEMA ... FROM BACKUP SET`
   then pick the table out of the restored schema).
4. Verify: `icebackup verify --source <orig> --restored <restored>` (row count + HASH_AGG diff).
5. Swap data back **into the original object** so its backup set keeps working:
   `CALL BACKUP_ADMIN.POLICIES.SWAP_BACK('<orig>', '<restored>');` (DELETE + INSERT SELECT in one transaction).
   **Do not** drop the original and rename the restored copy — the backup set is bound to the original ID.
6. Resume writers. Take a manual backup: `ALTER BACKUP SET <SET> ADD BACKUP;`
7. Drop the restored copy once signed off.
