import pytest

from icebackup import config, guards


def _raw(**over):
    raw = {
        "env": "dev",
        "admin": {"database": "BACKUP_ADMIN", "schema": "POLICIES", "warehouse": "WH"},
        "replication_refresh_minutes": 60,
        "allow_retention_lock": False,
        "tiers": {"gold": {"schedule_minutes": 60, "expire_after_days": 7}},
        "targets": [{"name": "S1", "kind": "ICEBERG TABLE", "object": "DB.SCH.T", "tier": "gold"}],
    }
    raw.update(over)
    return raw


def test_valid_config_passes():
    assert guards.check(config.from_dict(_raw())) == []


def test_schedule_below_60_minutes_rejected():
    cfg = config.from_dict(_raw(tiers={"gold": {"schedule_minutes": 30, "expire_after_days": 7}}))
    assert any("minimum" in e for e in guards.check(cfg))


def test_policy_needs_schedule_or_expiry():
    cfg = config.from_dict(_raw(tiers={"gold": {}}))
    assert any("needs schedule" in e for e in guards.check(cfg))


def test_lock_blocked_outside_allowed_env():
    cfg = config.from_dict(_raw(tiers={"gold": {"schedule_minutes": 60, "expire_after_days": 7,
                                                "retention_lock": True}}))
    assert any("not allowed" in e for e in guards.check(cfg))


def test_lock_requires_ack_ticket():
    cfg = config.from_dict(_raw(allow_retention_lock=True,
                                tiers={"gold": {"schedule_minutes": 60, "expire_after_days": 7,
                                                "retention_lock": True}}))
    assert any("ack" in e for e in guards.check(cfg))


def test_expiry_must_exceed_replication_interval():
    cfg = config.from_dict(_raw(replication_refresh_minutes=20000))
    assert any("replication" in e for e in guards.check(cfg))


def test_invalid_kind_and_injection_rejected():
    cfg = config.from_dict(_raw(targets=[{"name": "S1; DROP DATABASE X", "kind": "EXTERNAL TABLE",
                                          "object": "DB.SCH.T", "tier": "gold"}]))
    errs = guards.check(cfg)
    assert any("kind" in e for e in errs) and any("invalid identifier" in e for e in errs)


def test_enforce_raises():
    with pytest.raises(guards.GuardError):
        guards.enforce(config.from_dict(_raw(tiers={"gold": {}})))


def test_shipped_env_configs_pass_guards():
    for env in ("dev", "stg"):
        assert guards.check(config.load(env)) == []
