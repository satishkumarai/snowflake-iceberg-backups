"""icebackup CLI: plan | apply | coverage | restore | verify."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from icebackup import config, coverage, guards, render, restore, verify


def _session(connection: str | None):
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        from snowflake.snowpark import Session
        builder = Session.builder
        return (builder.config("connection_name", connection) if connection else builder).create()


def cmd_plan(args) -> int:
    cfg = config.load(args.env)
    guards.enforce(cfg)
    out_dir = Path("build") / cfg.env
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, sql in render.render(cfg):
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sql)
        print(f"rendered {path}")
    return 0


def cmd_apply(args) -> int:
    cfg = config.load(args.env)
    guards.enforce(cfg)
    session = _session(args.connection)
    for rel, sql in render.render(cfg):
        for stmt in render.split_statements(sql):
            print(f"-- {rel}\n{stmt[:160]}...")
            if not args.dry_run:
                session.sql(stmt).collect()
    return 0


def cmd_coverage(args) -> int:
    session = _session(args.connection)
    result = coverage.scan(session, args.database)
    print(json.dumps(result, indent=2, default=str))
    return 1 if any(r["status"] != "ELIGIBLE" for r in result) and args.strict else 0


def cmd_restore(args) -> int:
    sql = restore.restore_sql(args.kind, args.target, args.set, args.backup_id)
    print(sql)
    if not args.dry_run:
        _session(args.connection).sql(sql).collect()
    return 0


def cmd_verify(args) -> int:
    result = verify.verify(_session(args.connection), args.source, args.restored)
    print(json.dumps(result))
    ok = result["content_match"] and result["src_rows"] == result["rst_rows"]
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="icebackup")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply"):
        sp = sub.add_parser(name)
        sp.add_argument("--env", required=True)
        sp.add_argument("--dry-run", action="store_true")
    sp = sub.add_parser("coverage")
    sp.add_argument("--database", required=True)
    sp.add_argument("--strict", action="store_true")
    sp = sub.add_parser("restore")
    sp.add_argument("--kind", default="ICEBERG TABLE")
    sp.add_argument("--set", required=True)
    sp.add_argument("--backup-id", required=True)
    sp.add_argument("--target", required=True)
    sp.add_argument("--dry-run", action="store_true")
    sp = sub.add_parser("verify")
    sp.add_argument("--source", required=True)
    sp.add_argument("--restored", required=True)
    args = p.parse_args(argv)
    return {"plan": cmd_plan, "apply": cmd_apply, "coverage": cmd_coverage,
            "restore": cmd_restore, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
