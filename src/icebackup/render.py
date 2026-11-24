"""Render templated SQL into an ordered list of (filename, sql) for a given config."""
from __future__ import annotations

from pathlib import Path
from string import Template

from icebackup.config import Config

SQL_ROOT = Path("sql")
STATIC = [
    "00_bootstrap/00_admin_objects.sql",
    "10_rbac/10_roles.sql",
    "10_rbac/20_grants.sql",
    "40_restore/swap_back.sql",
    "50_monitoring/50_views.sql",
]


def policy_name(tier: str) -> str:
    return f"{tier.upper()}_BACKUP_POLICY"


def _common(cfg: Config) -> dict[str, str]:
    return {"ADMIN_DB": cfg.admin_db, "ADMIN_SCHEMA": cfg.admin_schema, "WAREHOUSE": cfg.warehouse}


def _sub(text: str, values: dict[str, str]) -> str:
    # substitute() (not safe_) so a missing variable fails loudly at plan time.
    return Template(text).substitute(values)


def render(cfg: Config, root: Path = SQL_ROOT) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    common = _common(cfg)
    for rel in STATIC:
        out.append((rel, _sub((root / rel).read_text(), common)))

    used = {t.tier for t in cfg.targets}
    for tier in (cfg.tiers[name] for name in sorted(used)):
        tmpl = "20_policies/regulated_lock.sql" if tier.retention_lock else "20_policies/tier_policy.sql.tmpl"
        values = {
            **common,
            "POLICY_NAME": policy_name(tier.name),
            "SCHEDULE_MINUTES": str(tier.schedule_minutes),
            "EXPIRE_AFTER_DAYS": str(tier.expire_after_days),
            "TIER": tier.name,
            "LOCK_ACK": cfg.retention_lock_ack,
        }
        out.append((f"20_policies/{tier.name}.sql", _sub((root / tmpl).read_text(), values)))

    set_tmpl = (root / "30_backup_sets/backup_set.sql.tmpl").read_text()
    for t in cfg.targets:
        values = {
            **common,
            "SET_NAME": t.name,
            "KIND": t.kind,
            "OBJECT": t.object,
            "POLICY_NAME": policy_name(t.tier),
            "TIER": t.tier,
        }
        out.append((f"30_backup_sets/{t.name}.sql", _sub(set_tmpl, values)))
    return out


def split_statements(sql: str) -> list[str]:
    """Split on ';' outside $$ blocks and quotes; drop comment-only fragments."""
    stmts, buf, in_dollar, in_quote, i = [], [], False, False, 0
    while i < len(sql):
        if not in_quote and sql.startswith("$$", i):
            in_dollar = not in_dollar
            buf.append("$$")
            i += 2
            continue
        ch = sql[i]
        if ch == "'" and not in_dollar:
            in_quote = not in_quote
        if ch == ";" and not in_dollar and not in_quote:
            stmts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    stmts.append("".join(buf))
    cleaned = []
    for s in stmts:
        body = "\n".join(l for l in s.splitlines() if not l.strip().startswith("--")).strip()
        if body:
            cleaned.append(s.strip())
    return cleaned
