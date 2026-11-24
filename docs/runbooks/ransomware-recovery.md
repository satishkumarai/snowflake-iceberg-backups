# Runbook: suspected account compromise / ransomware

1. Security incident lead declares incident; rotate credentials, disable compromised users, review
   `LOGIN_HISTORY` / `QUERY_HISTORY`.
2. **Do not** alter backup policies or sets. Locked sets cannot be deleted by the attacker (or by you).
3. Identify last-known-good timestamp from `QUERY_HISTORY` of destructive statements.
4. Inventory protected objects: `SELECT * FROM BACKUP_ADMIN.MONITORING.V_BACKUP_INVENTORY;`
5. Restore **schemas/databases** under new names (`CREATE DATABASE <db>_RECOVERED FROM BACKUP SET ...`),
   validate, then cut consumers over or swap data back.
6. Unprotected objects (internal stages, pipes, streams, Cortex Search, semantic views, Streamlits,
   account objects) must be rebuilt from source control. Keep them in Git.
7. Post-incident: if a secondary region exists, compare backups there before failback.
