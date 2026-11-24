from icebackup.coverage import classify


def test_classify():
    assert classify({"catalog_name": "SNOWFLAKE", "external_volume_name": "SNOWFLAKE_MANAGED"}) == "ELIGIBLE"
    assert classify({"catalog_name": "GLUE_CAT"}) == "EXTERNAL_CATALOG_NOT_SUPPORTED"
    assert classify({"catalog_name": "SNOWFLAKE", "external_volume_name": "S3_VOL"}) \
        == "CUSTOMER_MANAGED_STORAGE_NOT_SUPPORTED"
    assert classify({"catalog_name": "SNOWFLAKE", "external_volume_name": "SNOWFLAKE_MANAGED",
                     "kind": "TRANSIENT"}) == "TRANSIENT_NOT_SUPPORTED"
