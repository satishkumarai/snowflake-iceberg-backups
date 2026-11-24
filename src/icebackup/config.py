"""Load base config and merge an environment overlay."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_KINDS = {"ICEBERG TABLE", "DYNAMIC ICEBERG TABLE", "SCHEMA", "DATABASE"}


@dataclass(frozen=True)
class Tier:
    name: str
    schedule_minutes: int | None
    expire_after_days: int | None
    retention_lock: bool


@dataclass(frozen=True)
class Target:
    name: str
    kind: str
    object: str
    tier: str


@dataclass(frozen=True)
class Config:
    env: str
    admin_db: str
    admin_schema: str
    warehouse: str
    replication_refresh_minutes: int
    allow_retention_lock: bool
    retention_lock_ack: str
    tiers: dict[str, Tier]
    targets: list[Target]


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load(env: str, root: Path = Path("config")) -> Config:
    base = yaml.safe_load((root / "base.yml").read_text())
    overlay = yaml.safe_load((root / "envs" / f"{env}.yml").read_text()) or {}
    raw = _deep_merge(base, overlay)
    return from_dict(raw)


def from_dict(raw: dict) -> Config:
    tiers = {
        name: Tier(
            name=name,
            schedule_minutes=t.get("schedule_minutes"),
            expire_after_days=t.get("expire_after_days"),
            retention_lock=bool(t.get("retention_lock", False)),
        )
        for name, t in raw["tiers"].items()
    }
    targets = [Target(**t) for t in raw.get("targets", [])]
    return Config(
        env=raw["env"],
        admin_db=raw["admin"]["database"],
        admin_schema=raw["admin"]["schema"],
        warehouse=raw["admin"]["warehouse"],
        replication_refresh_minutes=int(raw.get("replication_refresh_minutes", 60)),
        allow_retention_lock=bool(raw.get("allow_retention_lock", False)),
        retention_lock_ack=str(raw.get("retention_lock_ack", "") or ""),
        tiers=tiers,
        targets=targets,
    )
