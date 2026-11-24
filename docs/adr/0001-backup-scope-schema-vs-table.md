# ADR-0001: Prefer schema-scoped backup sets for Iceberg tables that get replaced

**Status:** Accepted

## Context
A backup set binds to the internal ID of its object. `CREATE OR REPLACE ICEBERG TABLE` creates a new ID,
orphaning a table-level set (no new backups can be added). Dynamic Iceberg tables reference base tables;
a table-level backup restores the DT but not its inputs.

## Decision
- Default to **SCHEMA** sets for schemas holding pipelines (base Iceberg tables + dynamic Iceberg tables).
- Use **ICEBERG TABLE / DYNAMIC ICEBERG TABLE** sets only for stable, never-replaced tables needing a
  different tier than their schema.
- Always use explicit `ICEBERG` / `DYNAMIC ICEBERG` keywords; do not rely on
  `DEFAULT_METADATA_WRITE_FORMAT = ICEBERG` promotion.

## Consequences
Schema backups silently skip transient, external-catalog, and customer-managed-volume Iceberg tables.
`icebackup coverage` must run in CI and alert on gaps.
