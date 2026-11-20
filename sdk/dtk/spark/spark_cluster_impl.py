from typing import Optional

from pyspark.sql import SparkSession


def make_spark_cluster(master_url: str, conf: Optional[dict] = None) -> SparkSession:
    """master_url: Spark standalone, e.g. spark://spark-master:7077."""
    builder = SparkSession.builder.master(master_url).appName("dtk")
    for k, v in (conf or {}).items():
        builder = builder.config(k, v)
    return builder.getOrCreate()
