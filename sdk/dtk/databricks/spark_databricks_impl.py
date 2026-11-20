from pyspark.sql import SparkSession


def make_spark_databricks() -> SparkSession:
    """The runtime's session."""
    return SparkSession.builder.getOrCreate()
