# ADR-0002: Retention lock is a governed, irreversible change

**Status:** Accepted

## Context
Applying a locked policy cannot be undone, even by Snowflake Support. Locked sets block DROP of the set,
schema, database, and account while unexpired backups exist. Expiry can be increased, never decreased.
Storage for every retained micro-partition is billed for the full period.

## Decision
- Locked policies live only in `sql/20_policies/regulated_lock.sql`, owned by security + compliance.
- `RETENTION_LOCK_ADMIN` is the only role granted `APPLY BACKUP RETENTION LOCK`; no human uses
  ACCOUNTADMIN to apply it.
- `apply` refuses lock policies unless `allow_retention_lock: true` **and** `retention_lock_ack` is set.
- Before apply, `icebackup plan` prints projected retained bytes from `BACKUP_STORAGE_USAGE` of the
  unlocked equivalent run for at least 7 days.
- Lock sets live in a database never used for scratch work (it cannot be dropped).

## Consequences
Slower to roll out; deliberately so.
