from typing import Optional

from pyspark.sql import SparkSession


def make_spark_local(conf: Optional[dict] = None) -> SparkSession:
    builder = SparkSession.builder.master("local[*]").appName("dtk")
    for k, v in (conf or {}).items():
        builder = builder.config(k, v)
    return builder.getOrCreate()
