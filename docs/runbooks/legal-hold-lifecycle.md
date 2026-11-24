# Runbook: legal hold lifecycle

**Role:** LEGAL_HOLD_ADMIN (holds `APPLY LEGAL HOLD`). Requires Business Critical+.

1. Legal provides scope + timeframe; map to backup sets via `V_BACKUP_INVENTORY`.
2. Add hold:
   `ALTER BACKUP SET <SET> MODIFY BACKUP IDENTIFIER '<id>' ADD LEGAL HOLD;`
3. **Immediately refresh** every failover/replication group containing `BACKUP_ADMIN`:
   `ALTER FAILOVER GROUP <fg> REFRESH;` (run in each secondary). Skipping this can erase the hold on failback.
4. Record ticket, backup id, timestamp in the legal register.
5. Release (only on written approval): `... REMOVE LEGAL HOLD;` then refresh again.
   Normal expiry resumes; if already past `expire_on`, it is deleted on the next expiration run.
