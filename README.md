# snowflake-iceberg-backups

Declarative, guarded management of **Snowflake Backups** for **Snowflake Storage for Apache Iceberg™ tables**
and **dynamic Iceberg tables** (GA on AWS, Nov 2026).

Backups are zero-copy, immutable, point-in-time snapshots grouped in **backup sets** and governed by
**backup policies** (schedule, expiry, optional irreversible **retention lock**). This repo turns that into
tiered, reviewable infrastructure with restore runbooks, coverage checks, and CI.

## Why this exists
Hand-rolled "clone + task + cleanup" backups have no immutability, no naming discipline, and silently
miss tables. This repo:
- Defines backup **tiers** in YAML (`config/`), rendered into SQL (`sql/`).
- Enforces **guards** before apply (`src/icebackup/guards.py`): no lock outside prod, expiry > replication
  interval, lock requires a cost acknowledgement, minimum 60-minute schedule.
- Reports **coverage gaps**: Iceberg tables that schema/database backups silently skip
  (transient, external-catalog, customer-managed volume).
- Ships **restore runbooks** that keep the backup set usable (swap data back; never rename).

## Quickstart
```bash
pip install -e ".[dev]"
make test                                   # unit tests, no Snowflake needed
icebackup plan  --env dev                   # render SQL to ./build/dev, compile-only check
icebackup apply --env dev                   # execute (refuses lock policies outside prod)
icebackup coverage --env dev                # list unprotected / unsupported Iceberg tables
icebackup restore --env dev --set GOLD_SALES_BS --backup-id <uuid> --target ORDERS_RESTORED
icebackup verify  --source SALES.CORE.ORDERS --restored SALES.CORE.ORDERS_RESTORED
```
Connection: standard `~/.snowflake/connections.toml` (`--connection` flag) or Snowpark active session.

## Layout
| Path | Purpose | Owner |
|---|---|---|
| `config/` | Tiers + per-env overlays | platform-eng |
| `sql/00-50` | Bootstrap, RBAC, policies, sets, restore, monitoring | platform-eng |
| `sql/20_policies/regulated_lock.sql` | Retention-locked policy (irreversible) | security + 2 approvers |
| `src/icebackup/` | CLI: plan / apply / coverage / restore / verify | platform-eng |
| `docs/adr/` | Architecture decisions | architecture |
| `docs/runbooks/` | On-call procedures | SRE |

## Validation
All SQL was run in a live AWS account; results and caveats are in [`docs/validation.md`](docs/validation.md).

## Decision guide
- **Use** for Snowflake-managed Iceberg tables on AWS needing point-in-time recovery, ransomware
  resilience, or SEC 17a-4 / FINRA 4511-style immutability (lock/legal hold need Business Critical+).
- **Don't use** for Iceberg on customer-managed volumes or external catalogs (unsupported — protect at
  the storage/catalog layer), transient tables, or as a replacement for cross-region DR (pair with
  account replication).

⭐ **If you find this project useful, please consider giving it a Star on GitHub!**

Your support helps increase visibility, encourages further development, and motivates me to share more Snowflake open-source projects.

🔗 [Star this repository on GitHub](https://github.com/satishkumarai/snowflake-iceberg-backups)
