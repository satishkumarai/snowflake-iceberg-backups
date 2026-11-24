from icebackup import config, render, restore


def test_dev_render_uses_explicit_iceberg_keywords():
    files = dict(render.render(config.load("dev")))
    assert "FOR ICEBERG TABLE ICEBERG_BACKUP_LAB.CORE.ORDERS_ICE" in files["30_backup_sets/LAB_ORDERS_BS.sql"]
    assert "FOR DYNAMIC ICEBERG TABLE" in files["30_backup_sets/LAB_ORDERS_DT_BS.sql"]
    assert "WITH RETENTION LOCK" not in "".join(files.values())


def test_no_unrendered_placeholders():
    for _, sql in render.render(config.load("dev")):
        assert "${" not in sql


def test_split_keeps_procedure_body_intact():
    sql = "SELECT 1;\nCREATE PROCEDURE p() RETURNS INT LANGUAGE SQL AS $$ BEGIN RETURN 1; END; $$;\n-- c\n"
    stmts = render.split_statements(sql)
    assert len(stmts) == 2 and "RETURN 1; END;" in stmts[1]


def test_restore_never_uses_or_replace_and_validates_uuid():
    sql = restore.restore_sql("ICEBERG TABLE", "DB.S.T_RESTORED", "BA.P.SET1",
                              "b5624ef0-1f35-452f-b132-09d8f0592e52")
    assert sql.startswith("CREATE ICEBERG TABLE") and "OR REPLACE" not in sql
    try:
        restore.restore_sql("ICEBERG TABLE", "T", "S", "x'; DROP TABLE y; --")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
