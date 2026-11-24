# ADR-0003: Backup sets and policies live in a dedicated BACKUP_ADMIN database

**Status:** Accepted

## Decision
- Policies and sets in `BACKUP_ADMIN.POLICIES` (same schema -> fewer refresh failures).
- `BACKUP_ADMIN` in its own failover group, refreshed at `replication_refresh_minutes`.
- Initial refresh order: policy group first, then set group.
- `expire_after_days * 1440 > replication_refresh_minutes` (guard), so every backup replicates at least once.
- After any legal hold change: **refresh immediately** (runbook) or failback may erase the hold.

## Consequences
First refresh of a separate group triggers a one-time full data transfer. Refresh latency grows with
the number of backups created since last refresh.
