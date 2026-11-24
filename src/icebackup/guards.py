"""Pre-apply safety checks. Every rule maps to an ADR or a documented Snowflake restriction."""
from __future__ import annotations

import re

from icebackup.config import VALID_KINDS, Config

MIN_SCHEDULE_MINUTES = 60
_IDENT = re.compile(r'^([A-Za-z_][A-Za-z0-9_$]*|"[^"]+")(\.([A-Za-z_][A-Za-z0-9_$]*|"[^"]+")){0,2}$')


class GuardError(ValueError):
    pass


def check(cfg: Config) -> list[str]:
    """Return a list of violations (empty means safe to apply)."""
    errors: list[str] = []
    for tier in cfg.tiers.values():
        if tier.schedule_minutes is None and tier.expire_after_days is None:
            errors.append(f"tier {tier.name}: needs schedule_minutes and/or expire_after_days")
        if tier.schedule_minutes is not None and tier.schedule_minutes < MIN_SCHEDULE_MINUTES:
            errors.append(f"tier {tier.name}: schedule {tier.schedule_minutes}m < {MIN_SCHEDULE_MINUTES}m minimum")
        if tier.expire_after_days is not None and tier.expire_after_days * 1440 <= cfg.replication_refresh_minutes:
            errors.append(f"tier {tier.name}: expiry must exceed replication refresh interval (ADR-0003)")
        if tier.retention_lock:
            if not cfg.allow_retention_lock:
                errors.append(f"tier {tier.name}: retention lock not allowed in env {cfg.env} (ADR-0002)")
            elif not cfg.retention_lock_ack:
                errors.append(f"tier {tier.name}: retention lock requires retention_lock_ack change ticket")
    names = [t.name for t in cfg.targets]
    if len(names) != len(set(names)):
        errors.append("duplicate backup set names in targets")
    for t in cfg.targets:
        if t.kind not in VALID_KINDS:
            errors.append(f"target {t.name}: kind {t.kind!r} not in {sorted(VALID_KINDS)}")
        if t.tier not in cfg.tiers:
            errors.append(f"target {t.name}: unknown tier {t.tier}")
        for ident in (t.name, t.object):
            if not _IDENT.match(ident):
                errors.append(f"target {t.name}: invalid identifier {ident!r}")
    return errors


def enforce(cfg: Config) -> None:
    errors = check(cfg)
    if errors:
        raise GuardError("guard violations:\n  - " + "\n  - ".join(errors))
