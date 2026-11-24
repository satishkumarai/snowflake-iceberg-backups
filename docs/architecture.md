# Architecture

## Before: hand-rolled clones
```mermaid
flowchart LR
  T[Task on cron] --> C[CREATE TABLE x_YYYYMMDD CLONE x]
  C --> N[Naming convention + tags]
  N --> P[Cleanup task drops old clones]
  P -.->|ACCOUNTADMIN can drop anything| R((Ransomware / insider risk))
```

## After: policy-driven backup sets
```mermaid
flowchart LR
  subgraph BACKUP_ADMIN DB
    POL[Backup policies: gold / silver / regulated+lock]
    BS[Backup sets]
  end
  ICE[(Snowflake-managed Iceberg tables)] --> BS
  DIT[(Dynamic Iceberg tables)] --> BS
  SCH[(Schemas containing both)] --> BS
  POL --> BS
  BS -->|CREATE ICEBERG TABLE ... FROM BACKUP SET| RST[Restored copy]
  RST -->|TRUNCATE + INSERT SELECT| ICE
  BS --> MON[ACCOUNT_USAGE views -> monitoring views -> alerts]
  BS -->|failover group| DR[Secondary region]
```

## Trust boundaries
| Role | Can | Cannot |
|---|---|---|
| BACKUP_ADMIN | create policies/sets, add/delete backups (unlocked) | apply locks, legal holds |
| BACKUP_OPERATOR | add backups, restore | create policies, delete backups |
| RETENTION_LOCK_ADMIN | create/apply locked policies | anything else |
| LEGAL_HOLD_ADMIN | add/remove legal holds | create/delete backups |
| BACKUP_AUDITOR | read monitoring views | change anything |
