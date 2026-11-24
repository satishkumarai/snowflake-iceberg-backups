-- !!! IRREVERSIBLE !!!  ADR-0002. Requires: role RETENTION_LOCK_ADMIN, Business Critical+,
-- env.allow_retention_lock = true, env.retention_lock_ack = <change ticket>.
-- Once applied to a set: backups cannot be deleted by any role, expiry can only increase,
-- and the set / schema / database / account cannot be dropped while unexpired backups exist.
USE ROLE RETENTION_LOCK_ADMIN;
CREATE BACKUP POLICY IF NOT EXISTS ${ADMIN_DB}.${ADMIN_SCHEMA}.${POLICY_NAME}
  WITH RETENTION LOCK
  SCHEDULE = '${SCHEDULE_MINUTES} MINUTE'
  EXPIRE_AFTER_DAYS = ${EXPIRE_AFTER_DAYS}
  COMMENT = 'tier=${TIER} RETENTION LOCK ticket=${LOCK_ACK} managed-by=icebackup';
