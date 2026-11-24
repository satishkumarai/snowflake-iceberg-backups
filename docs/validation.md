# Validation log

Account XT18858, region AWS_AP_NORTHEAST_1, edition below Business Critical, run 2026-11-21.
Every row was **executed** unless marked compile-only.

| Check | Result |
|---|---|
| Bootstrap, RBAC (5 roles), grants incl. `APPLY BACKUP RETENTION LOCK` / `APPLY LEGAL HOLD` | OK |
| Policies gold (60 MINUTE / 2 d), silver (1440 MINUTE / 3 d), created as BACKUP_ADMIN | OK |
| Sets `FOR SCHEMA`, `FOR ICEBERG TABLE`, `FOR DYNAMIC ICEBERG TABLE` + `ADD BACKUP` | OK; `ADD BACKUP` 1.2–2.7 s |
| `SHOW BACKUP SETS` object_kind for Iceberg / dynamic Iceberg sets | Reported as `TABLE` |
| Manual backup inherits policy expiry | expire_on = created_on + 3 days |
| 1M-row Iceberg table, DELETE 50%, `CREATE ICEBERG TABLE ... FROM BACKUP SET` | 3.2 s; row count and HASH_AGG match pre-delete copy |
| `SWAP_BACK` into original, then `ADD BACKUP` to the same set | Original repaired; set keeps accepting backups |
| `CREATE DYNAMIC ICEBERG TABLE ... FROM BACKUP SET` | Restored in SUSPENDED state |
| `CREATE SCHEMA ... FROM BACKUP SET` | Iceberg tables restored with new base_location; DT restored SUSPENDED and its fully-qualified query still reads the **original** `CORE.ORDERS_ICE` |
| Fix: recreate restored DT against `CORE_RESTORED.ORDERS_ICE` | ACTIVE; SUM(orders) 1,000,000 = base rows; revenue matches |
| ACCOUNT_USAGE re-check 8 min after first backup | BACKUP_SETS / BACKUPS still 0 rows (latency); INFORMATION_SCHEMA.BACKUPS still listed dropped `SCRATCH_BS` 6 min after DROP |
| Delete a non-oldest backup | Rejected: "not the oldest active backup without a legal hold" |
| `ADD BACKUP` after `CREATE OR REPLACE` of the subject table | Rejected: "Target object for Backup Set ... does not exist or not authorized" |
| Backup set on a transient Iceberg table | Rejected: "it is a transient table" |
| Legal hold | Rejected: "cannot be applied on accounts below Business Critical Edition" |
| Retention-locked policy | **Compile-only** (irreversible); confirmed not created |
| Stale-backup alert | Compile-only (needs your email integration) |
| Drop an unlocked set that still holds an unexpired backup | Allowed |
| Monitoring views | Created and queried. Minutes after creation ACCOUNT_USAGE BACKUP_SETS/BACKUPS returned 0 rows (latency) while `BACKUP_ADMIN.INFORMATION_SCHEMA.BACKUPS` returned 5; BACKUP_OPERATION_HISTORY already had rows |

Not measured: storage cost (BACKUP_STORAGE_USAGE not yet populated), scheduled-backup behavior over
hours/days, replication, retention lock behavior.
