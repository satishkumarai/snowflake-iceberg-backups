-- DEV ONLY. icebackup refuses to render this if any policy in ADMIN_DB has a retention lock.
DROP BACKUP SET IF EXISTS ${ADMIN_DB}.${ADMIN_SCHEMA}.${SET_NAME};
